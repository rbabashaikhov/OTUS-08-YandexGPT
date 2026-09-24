import json
import os
from pathlib import Path

from dotenv import load_dotenv
from yandex_ai_studio_sdk import AIStudio


load_dotenv()

YC_API_KEY = os.getenv("YC_API_KEY")
YC_FOLDER_ID = os.getenv("YC_FOLDER_ID")

import csv

from data_utils import load_documents

import re


# -------------------------
# Настройка модели
# -------------------------

sdk = AIStudio(
    folder_id=YC_FOLDER_ID,
    auth=YC_API_KEY,
)

model = sdk.models.completions("yandexgpt-lite")

model = model.configure(
    temperature=0.1,
    max_tokens=2000,
)


# -------------------------
# Промпты
# -------------------------

SYSTEM_PROMPT = """
Ты — точный AI-помощник юриста, специализирующийся на извлечении
структурированных фактов из судебных документов.

Твоя задача — извлекать только информацию, явно присутствующую
в предоставленном тексте документа.

Правила:

1. Не придумывай отсутствующие данные и не дополняй текст
   информацией из собственных знаний.

2. Если значение отсутствует в предоставленном тексте
   или его нельзя надежно определить, возвращай null.

3. Не восстанавливай анонимизированные данные.
   Значения вида <ДАТА>, <ФИО>, <НОМЕР>, <АДРЕС>,
   <ОБЕЗЛИЧЕНО> и аналогичные placeholders
   не пытайся расшифровывать или угадывать.

4. Не путай номера судебного дела с номерами протоколов,
   актов, постановлений и других документов.

5. Не путай дату текущего судебного документа
   с датами правонарушений, протоколов, проверок,
   предыдущих решений и других событий.

6. Не путай роли разных участников судебного дела.
   Определяй роль лица только на основании текста.

7. При извлечении статей закона используй только статьи
   и нормативные акты, явно упомянутые в тексте.
   Не добавляй статьи самостоятельно.

8. При извлечении результата рассмотрения дела используй
   фактически принятое судом решение.

9. Если в тексте присутствует резолютивная часть после слов
   "ПОСТАНОВИЛ", "РЕШИЛ", "ОПРЕДЕЛИЛ"
   или аналогичной формулировки, она имеет приоритет
   при определении решения суда.

10. Не путай фактически принятое решение суда
    с возможными санкциями, перечисленными в статье закона.

11. Не используй максимальный или минимальный возможный
    размер наказания вместо фактически назначенного судом.

12. Если в предоставленном тексте отсутствует резолютивная часть
    и фактическое решение суда невозможно надежно определить,
    возвращай null для соответствующих значений.

13. Ответ должен содержать только валидный JSON-объект.

14. Не добавляй Markdown-разметку, пояснения,
    комментарии или текст до и после JSON.

15. Не используй комментарии // или /* */ внутри JSON.

16. Используй двойные кавычки для ключей
    и строковых значений JSON.

17. Ответ должен корректно обрабатываться
    функцией json.loads() в Python.
"""


USER_PROMPT_TEMPLATE = """
Извлеки из судебного документа следующие сущности:

- case_number:
  номер текущего судебного дела.

- document_date:
  дата текущего судебного решения, постановления
  или определения.

- persons:
  список лиц, упомянутых в документе.
  Для каждого лица укажи:
  - name — ФИО или имя лица;
  - role — его роль в судебном деле.

- law_articles:
  список статей законов и нормативных актов,
  явно упомянутых в документе.

- court_decision:
  сведения о фактически принятом судом решении:
  - type — вид решения, наказания или взыскания;
  - amount — денежная сумма, если она назначена судом;
  - currency — валюта суммы;
  - term — фактически назначенный срок, если он есть.

Для court_decision используй именно итоговое решение суда.
В первую очередь ориентируйся на резолютивную часть после слов
"ПОСТАНОВИЛ", "РЕШИЛ", "ОПРЕДЕЛИЛ" или аналогичных формулировок.

Не используй в качестве court_decision возможные санкции статьи,
если они только перечислены в тексте и фактически судом не назначены.

Если какого-либо значения нет или его невозможно надежно
определить из предоставленного текста, используй null.

Верни ТОЛЬКО валидный JSON следующей структуры:

{{
  "case_number": null,
  "document_date": null,
  "persons": [
    {{
      "name": null,
      "role": null
    }}
  ],
  "law_articles": [],
  "court_decision": {{
    "type": null,
    "amount": null,
    "currency": null,
    "term": null
  }}
}}

Текст документа:

{text}
"""


# -------------------------
# Функции
# -------------------------

def build_messages(text: str) -> list[dict[str, str]]:
    """
    Формирует список сообщений для YandexGPT.
    """
    return [
        {
            "role": "system",
            "text": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "text": USER_PROMPT_TEMPLATE.format(text=text),
        },
    ]


def extract_entities(text: str) -> str:
    """
    Отправляет юридический текст в YandexGPT
    и возвращает сырой ответ модели.
    """
    messages = build_messages(text)

    result = model.run(messages)

    return result[0].text


def clean_response(response: str) -> str:
    """
    Очищает ответ модели перед JSON-парсингом:
    - удаляет Markdown-блоки ```json ... ```
    - удаляет однострочные комментарии //
    """
    text = response.strip()

    if text.startswith("```json"):
        text = text.removeprefix("```json")
    elif text.startswith("```"):
        text = text.removeprefix("```")

    if text.endswith("```"):
        text = text.removesuffix("```")

    text = re.sub(r"//.*$", "", text, flags=re.MULTILINE)

    return text.strip()


def parse_response(response: str) -> dict:
    try:
        return json.loads(response)
    except json.JSONDecodeError as error:
        print("Ошибка парсинга JSON:")
        print(error)
        return {}


def save_response(response: dict, filename: str) -> None:
    """
    Сохраняет результат в JSON-файл.
    """
    output_path = Path(filename)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(
            response,
            file,
            ensure_ascii=False,
            indent=2,
        )


def process_document(text: str, filename: str) -> dict:
    """
    Выполняет весь NER-пайплайн для одного документа.
    """
    raw_response = extract_entities(text)
    cleaned_response = clean_response(raw_response)
    parsed_response = parse_response(cleaned_response)

    save_response(
        parsed_response,
        filename,
    )

    return parsed_response


def process_documents(
    documents: list[str],
    output_dir: str,
) -> list[dict]:
    """
    Обрабатывает несколько юридических документов.
    """
    results = []

    for i, document in enumerate(documents, start=1):
        print(f"\nОбработка документа {i}/{len(documents)}")

        try:
            result = process_document(
                document,
                f"{output_dir}/result_{i:02d}.json",
            )

            if result:
                results.append(result)
                print(f"OK: документ {i}")
            else:
                print(f"ERROR: документ {i} вернул пустой результат")

        except Exception as error:
            print(f"ERROR: документ {i}")
            print(error)

    return results

# -------------------------
# Тест
# -------------------------

if __name__ == "__main__":
    documents = load_documents(
        "ner_homework/data/test.csv",
        limit=30,
    )

    print("Загружено документов:", len(documents))

    results = process_documents(
        documents,
        "ner_homework/results",
    )

    print()
    print("Успешно обработано:", len(results))