import csv


DATASET_PATH = "ner_homework/data/test.csv"


def find_document(
    filename: str,
    keywords: list[str],
    tail_chars: int = 3000,
) -> str | None:
    """
    Ищет документ, в последних tail_chars символах которого
    встречаются все переданные ключевые слова.
    """
    with open(filename, "r", encoding="utf-8") as file:
        reader = csv.reader(file)

        for row in reader:
            if not row:
                continue

            text = row[0]
            text_tail = text[-tail_chars:].lower()

            if all(keyword.lower() in text_tail for keyword in keywords):
                return text

    return None


if __name__ == "__main__":
    document = find_document(
        DATASET_PATH,
        [
            "назначить наказание",
            "штраф",
            "рублей",
        ],
        tail_chars=3000,
    ),
       

    if document is not None:
        print("Документ найден")
        print("Длина:", len(document))
        print()
        print(document[-3000:])
    else:
        print("Документ не найден")