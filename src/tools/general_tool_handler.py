import os
import shutil
import sqlite3
import re

import pandas as pd
import requests

from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI

from .prompts import get_translate_prompt

class GeneralToolHandler:
    def __init__(self) -> None:
        # TODO add a config class to load all these configurations
        self.model_name = 'gpt-3.5-turbo-0125'
        self.llm = ChatOpenAI(model=self.model_name)
        translate_prompt = get_translate_prompt()
        self.translator = translate_prompt | self.llm
        self.k = 2
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
        self.db_url = "https://storage.googleapis.com/benchmarks-artifacts/travel-db/travel2.sqlite"
        self.local_file = "travel2.sqlite"
        self.backup_file = "travel2.backup.sqlite"
        self.policy_file = "files/alibaba.md"
        self.chroma_persist_dir = 'files/chroma/'
        self.chroma_collection_name = 'policy'
        self.init_db()
        self._init_retriever()

    def init_db(self):
        overwrite = False
        if overwrite or not os.path.exists(self.local_file):
            response = requests.get(self.db_url)
            response.raise_for_status()  # Ensure the request was successful
            with open(self.local_file, "wb") as f:
                f.write(response.content)
            # Backup - we will use this to "reset" our DB in each section
            shutil.copy(self.local_file, self.backup_file)
        # Convert the flights to present time for our tutorial
        conn = sqlite3.connect(self.local_file)
        cursor = conn.cursor()

        tables = pd.read_sql(
            "SELECT name FROM sqlite_master WHERE type='table';", conn
        ).name.tolist()
        tdf = {}
        for t in tables:
            tdf[t] = pd.read_sql(f"SELECT * from {t}", conn)

        example_time = pd.to_datetime(
            tdf["flights"]["actual_departure"].replace("\\N", pd.NaT)
        ).max()
        current_time = pd.to_datetime("now").tz_localize(example_time.tz)
        time_diff = current_time - example_time

        tdf["bookings"]["book_date"] = (
            pd.to_datetime(tdf["bookings"]["book_date"].replace("\\N", pd.NaT), utc=True)
            + time_diff
        )

        datetime_columns = [
            "scheduled_departure",
            "scheduled_arrival",
            "actual_departure",
            "actual_arrival",
        ]
        for column in datetime_columns:
            tdf["flights"][column] = (
                pd.to_datetime(tdf["flights"][column].replace("\\N", pd.NaT)) + time_diff
            )

        for table_name, df in tdf.items():
            df.to_sql(table_name, conn, if_exists="replace", index=False)
        del df
        del tdf
        conn.commit()
        conn.close()

        self.db = self.local_file  # We'll be using this local file as our DB in this tutorial


    def _init_retriever(self):
        if self._vector_db_initiated_before():
            self.vector_db = Chroma(collection_name=self.chroma_collection_name, 
                                    persist_directory=self.chroma_persist_dir, 
                                    embedding_function=self.embeddings)
        else:
            # create the vector db and add embeddings
            with open(self.policy_file, 'r') as f:
                faq_text = f.read()

            # docs = [{"page_content": txt} for txt in re.split(r"(?=\n##)", faq_text)]
            texts = re.split(r"(?=\n##)", faq_text)

            self.vector_db = Chroma.from_texts(texts=texts,
                                              embedding=self.embeddings, 
                                              persist_directory=self.chroma_persist_dir, 
                                              collection_name=self.chroma_collection_name)
        # self.retriever = self.vector_db.as_retriever()

    def _vector_db_initiated_before(self):
        # TODO a better checking method
        db_file_path = os.path.join(self.chroma_persist_dir,"chroma.sqlite3")
        return os.path.exists(db_file_path)
    
    def lookup_policy(self, query: str):
        query = self.translator.invoke({'query':query}).content

        retriever = self.vector_db.as_retriever(search_kwargs={"k": self.k})
        docs = retriever.invoke(query)

        return '\n\n'.join(d.page_content for d in docs)