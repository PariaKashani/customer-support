import shutil
import uuid

from src.agent import CustomerSupportAgent

if __name__=="__main__":
    db = "travel2.sqlite"
    backup_file = "travel2.backup.sqlite"

    shutil.copy(backup_file, db)
    thread_id = str(uuid.uuid4())

    config = {
    "configurable": {
        # The passenger_id is used in our flight tools to
        # fetch the user's flight information
        "passenger_id": "3442 587242",
        # Checkpoints are accessed by thread_id
        "thread_id": thread_id,
    }
    }

    questions = [
    "سلام، پرواز من چه زمانی است؟",
    "آیا اجازه دارم پروازم رو به زمانی زودتر موکول کنم؟ من دوست دارم همین امروز برم.",
    "پس پروازم رو به زمانی توی هفته ی آینده تغییر بده.",
    "گزینه ی موجود بعدی عالی هست.",
    "در مورد اسکان و حمل و نقل چطور؟",
    "بله، فکر می کنم برای اقامت یک هفته ای خود (7 روز) یک هتل مقرون به صرفه می خواهم. و من می خواهم یک ماشین اجاره کنم.",
    "می تونید هتلی که پیشنهاد کردید رو برام رزرو کنید؟ به نظر خوب میاد.",
    "بله، ادامه دهید و هر چیزی را که هزینه متوسطی دارد و در دسترس است رزرو کنید.",
    "حالا برای ماشین، گزینه های من چیست؟",
    "عالیه ممنون، بیا ارزون ترین رو انتخاب کن و 7 روز برام رزروش کن",
    "خب حالا چه توصیه هایی برای گشت و گذار دارید؟",
    "آیا اینها در دسترس هستند زمانی که من اونجام؟",
    "جذابه، من موزه ها رو دوست دارم. کجا ها میتونم برم؟ ",
    "باشه عالیه، یکی رو بردار و برای دومین روز اقامت من اونجا برام رزروش کن.",
    ]

    agent = CustomerSupportAgent(model_name='gpt-3.5-turbo-0125')

    for question in questions:
        agent.run(question, config)