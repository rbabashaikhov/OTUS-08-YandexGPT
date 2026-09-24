import csv

documents = []

MAX_CHARS = 6000


def prepare_text(text: str, max_chars: int = MAX_CHARS) -> str:
    """
    Очищает текст и ограничивает его длину.

    Для длинных судебных документов сохраняет начало и конец:
    в начале обычно находятся номер дела, дата и участники,
    а в конце — резолютивная часть решения суда.
    """
    text = text.replace("\xa0", " ")
    text = text.strip()

    if len(text) <= max_chars:
        return text

    half = max_chars // 2

    start = text[:half]
    end = text[-half:]

    return start + "\n\n[... ЧАСТЬ ДОКУМЕНТА ПРОПУЩЕНА ...]\n\n" + end


def load_documents( filename: str, limit: int | None = None,) -> list[str]:
    """
    Загружает документы из CSV-файла.
    """
    documents = []

    with open(filename, "r", encoding="utf-8") as file:
        reader = csv.reader(file)

        for i, row in enumerate(reader):
            text = row[0]

            prepered_text = prepare_text(text)

            documents.append(prepered_text)

            if limit is not None and i + 1 >= limit:
                break

    return documents


with open("ner_homework/data/test.csv", "r", encoding="utf-8") as file:
    reader = csv.reader(file)

    for i, row in enumerate(reader):
        text = row[0]

        prepered_text = prepare_text(text)

        documents.append(prepered_text)





