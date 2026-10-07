import json
from pathlib import Path

from database import connect_to_database
from models import Author


def main():
    connect_to_database()
    authors_file = Path(__file__).resolve().with_name("authors.json")
    with authors_file.open(encoding="utf-8") as file:
        authors = json.load(file)

    for data in authors:
        Author.objects(fullname=data["fullname"]).update_one(
            upsert=True,
            set__born_date=data["born_date"],
            set__born_location=data["born_location"],
            set__description=data["description"],
        )

    print(f"Завантажено авторів: {len(authors)}")


if __name__ == "__main__":
    main()
