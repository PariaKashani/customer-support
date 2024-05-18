from typing import Literal

from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import ToolMessage

from .logger import Logger
from .models.state import State
from .models.assistant import Assistant
from .graph_utils import (user_info, create_entry_node, 
                          CompleteOrEscalate, create_route, 
                          pop_dialog_state, route_primary_assistant,
                          route_to_workflow)
from .tools.general_tools import get_primary_assistant_tools, create_tool_node_with_fallback
from .tools.flight_tools import get_flight_safe_tools, get_flight_sensitive_tools, ToFlightBookingAssistant
from .tools.car_rental_tools import get_car_safe_tools, get_car_sensitive_tools, ToBookCarRental
from .tools.hotel_booking_tools import get_hotel_safe_tools, get_hotel_sensitive_tools, ToHotelBookingAssistant
from .tools.excursion_booking_tools import get_excursion_safe_tools, get_excursion_sensitive_tools, ToBookExcursion
from .tools.prompts import (get_flight_booking_prompt, 
                            get_book_hotel_prompt, 
                            get_car_rental_prompt, 
                            get_book_excursion_prompt, 
                            get_primary_assistant_prompt)

class CustomerSupportAgent:
    def __init__(self, model_name='gpt-3.5-turbo-0125') -> None:
        # TODO get config file as input
        self.llm = ChatOpenAI(model=model_name)
        self.initialize_skills()
        self.init_primary_assistant()
        self.init_graph()
        self.logger = Logger()


    def initialize_skills(self):
        # this method initialized all the tools and returns an empty state
        self.skills = {'flight':{'tools':{'safe':get_flight_safe_tools(), 'sensitive':get_flight_sensitive_tools()},
                                 'assistant_name': "Flight Updates & Booking Assistant",
                                 'route':{"name":"update_flight",
                                          "type_hint":Literal["update_flight_sensitive_tools",
                                                              "update_flight_safe_tools",
                                                              "leave_skill",
                                                              "__end__",]},
                                 'prompt': get_flight_booking_prompt},
                       'hotel':{'tools':{'safe':get_hotel_safe_tools(), 'sensitive':get_hotel_sensitive_tools()},
                                'assistant_name': "Hotel Booking Assistant",
                                'route': {"name":"book_hotel",
                                          "type_hint":Literal["leave_skill", 
                                                              "book_hotel_safe_tools", 
                                                              "book_hotel_sensitive_tools", 
                                                              "__end__"]},
                                'prompt': get_book_hotel_prompt},
                       'car':{'tools':{'safe':get_car_safe_tools(), 'sensitive':get_car_sensitive_tools()},
                              'assistant_name':"Car Rental Assistant",
                              "route":{"name":"book_car_rental",
                                       "type_hint":Literal["book_car_rental_safe_tools",
                                                           "book_car_rental_sensitive_tools",
                                                           "leave_skill",
                                                           "__end__",]},
                              "prompt":get_car_rental_prompt},
                       'excursion':{'tools':{'safe':get_excursion_safe_tools(), 'sensitive':get_excursion_sensitive_tools()},
                                    'assistant_name':"Trip Recommendation Assistant",
                                    "route":{"name":"book_excursion",
                                             "type_hint":Literal["book_excursion_safe_tools",
                                                                 "book_excursion_sensitive_tools",
                                                                 "leave_skill",
                                                                 "__end__",]},
                                    "prompt":get_book_excursion_prompt}}
        
        self.skill_runnables = {k: self.get_runnable_skill(v['prompt'](), 
                                                           v['tools']['safe']+v['tools']['sensitive']) 
                                                           for k,v in self.skills.items()}
        

    def init_primary_assistant(self):
        primary_assistant_tools = get_primary_assistant_tools()
        self.assistant_runnable = get_primary_assistant_prompt() | self.llm.bind_tools(
            primary_assistant_tools
            + [
                ToFlightBookingAssistant,
                ToBookCarRental,
                ToHotelBookingAssistant,
                ToBookExcursion,
                ])
        
    def get_runnable_skill(self, prompt, tools):
        return prompt | self.llm.bind_tools(tools + [CompleteOrEscalate])
    
    def init_graph(self):
        builder = StateGraph(State)
        builder.add_node("fetch_user_info", user_info)
        builder.set_entry_point("fetch_user_info")

        for k, v in self.skills.items():
            builder.add_node(
            "enter_"+v["route"]["name"],
            create_entry_node(v["assistant_name"], v["route"]["name"]),
            )
            builder.add_node(v["route"]["name"], Assistant(self.skill_runnables[k]))
            builder.add_edge("enter_"+v["route"]["name"], v["route"]["name"])
            builder.add_node(
                v["route"]["name"] + "_sensitive_tools",
                create_tool_node_with_fallback(v['tools']['sensitive']),
            )
            builder.add_node(
                v["route"]["name"] + "_safe_tools",
                create_tool_node_with_fallback(v['tools']['safe']),
            )

            builder.add_edge(v["route"]["name"] + "_sensitive_tools", v["route"]["name"])
            builder.add_edge(v["route"]["name"] + "_safe_tools", v["route"]["name"])
            builder.add_conditional_edges(v["route"]["name"], create_route(v["tools"]["safe"], 
                                                                           v["route"]["name"], 
                                                                           v["route"]["type_hint"]))
        builder.add_node("leave_skill", pop_dialog_state)
        builder.add_edge("leave_skill", "primary_assistant")

        # Primary assistant
        builder.add_node("primary_assistant", Assistant(self.assistant_runnable))
        builder.add_node(
            "primary_assistant_tools", create_tool_node_with_fallback(get_primary_assistant_tools())
        )
        
        builder.add_conditional_edges(
             "primary_assistant",
             route_primary_assistant,
             {
                "enter_update_flight": "enter_update_flight",
                "enter_book_car_rental": "enter_book_car_rental",
                "enter_book_hotel": "enter_book_hotel",
                "enter_book_excursion": "enter_book_excursion",
                "primary_assistant_tools": "primary_assistant_tools",
                END: END,
            },
        )
        builder.add_edge("primary_assistant_tools", "primary_assistant")

        builder.add_conditional_edges("fetch_user_info", route_to_workflow)

        self.builder = builder

        # Compile graph
        self.memory = SqliteSaver.from_conn_string(":memory:")
        self.graph = builder.compile(
            checkpointer=self.memory,
            # Let the user approve or deny the use of sensitive tools
            interrupt_before=[
                "update_flight_sensitive_tools",
                "book_car_rental_sensitive_tools",
                "book_hotel_sensitive_tools",
                "book_excursion_sensitive_tools",
            ],
        )

    def run(self, question, config):
        events = self.graph.stream(
            {"messages": ("user", question)}, config, stream_mode="values"
        )

        for event in events:
            self.logger.log_event(event)

        snapshot = self.graph.get_state(config)
        while snapshot.next:
            # We have an interrupt! The agent is
            # trying to use a tool.
            # The user can approve or deny it
            user_input = input(
                "Do you approve of the above actions? Type 'y' to continue;"
                " otherwise, explain your requested changed.\n\n"
            )
            if user_input.strip() == "y":
                # Just continue
                result = self.graph.invoke(
                    None,
                    config,
                )
            else:
                # Satisfy the tool invocation by
                # providing instructions on the requested changes / change of mind
                result = self.graph.invoke(
                    {
                        "messages": [
                            ToolMessage(
                                tool_call_id=event["messages"][-1].tool_calls[0]["id"],
                                content=f"API call denied by user. Reasoning: '{user_input}'. Continue assisting, accounting for the user's input.",
                            )
                        ]
                    },
                    config,
                )
            snapshot = self.graph.get_state(config)

    
