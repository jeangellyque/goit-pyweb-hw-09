import json
from pathlib import Path

from database import connect_to_database
from models import Author, Quote


def main():
    connect_to_database()
    quotes_file = Path(__file__).resolve().with_name("quotes.json")
    with quotes_file.open(encoding="utf-8") as file:
        quotes = json.load(file)

    for data in quotes:
        author = Author.objects(fullname=data["author"]).first()
        if author is None:
            raise ValueError(
                f"Автор {data['author']!r} відсутній у колекції authors. "
                "Спочатку запустіть load_authors.py."
            )

        Quote.objects(quote=data["quote"], author=author).update_one(
            upsert=True,
            set__tags=data["tags"],
            set__author=author,
        )

    print(f"Завантажено цитат: {len(quotes)}")


if __name__ == "__main__":
    main()
