import os

from dotenv import load_dotenv
from yandex_ai_studio_sdk import AIStudio


load_dotenv()

YC_API_KEY = os.getenv("YC_API_KEY")
YC_FOLDER_ID = os.getenv("YC_FOLDER_ID")


sdk = AIStudio(
    folder_id=YC_FOLDER_ID,
    auth=YC_API_KEY,
)

model = sdk.models.completions("yandexgpt-lite")

model = model.configure(
    temperature=0.6,
    max_tokens=2000,
)

messages = [
    {
        "role": "system",
        "text": "Ты ассистент дроид, способный помочь в галактических приключениях.",
    },
    {
        "role": "user",
        "text": "Привет, Дроид! Мне нужна твоя помощь, чтобы узнать больше о Силе. Как я могу научиться ее использовать?",
    },
    {
        "role": "assistant",
        "text": "Привет! Чтобы овладеть Силой, тебе нужно понять ее природу. Сила находится вокруг нас и соединяет всю галактику. Начнем с основ медитации.",
    },
    {
        "role": "user",
        "text": "Хорошо, а как насчет строения светового меча? Это важная часть тренировки джедая. Как мне создать его?",
    },
]

result = model.run(messages)

for alternative in result:
    print(alternative.text)