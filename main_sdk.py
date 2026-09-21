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
    max_tokens=1000,
)

messages = [
    {
        "role": "system",
        "text": "Ты дружелюбный помощник. Отвечай кратко и понятно."
    }
]


while True:
    user_text = input("Ты: ")

    if user_text.lower() in ["exit", "quit", "выход"]:
        print("Чат завершён.")
        break

    messages.append(
        {
            "role": "user",
            "text": user_text
        }
    )

    result = model.run(messages)

    assistant_text = result[0].text

    print(f"YandexGPT: {assistant_text}")

    messages.append(
        {
            "role": "assistant",
            "text": assistant_text
        }
    )
