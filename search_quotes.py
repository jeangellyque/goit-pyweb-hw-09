import json
import re
import sys

from cache import create_cache_client
from database import connect_to_database
from models import Author, Quote

CACHE_TTL_SECONDS = 300


def serialize_quotes(quotes):
    return [
        {"quote": quote.quote, "author": quote.author.fullname}
        for quote in quotes
    ]


def find_quotes(operation, value):
    pattern = f"^{re.escape(value)}"
    if operation == "name":
        authors = list(Author.objects(fullname__iregex=pattern))
        if not authors:
            return []
        quotes = Quote.objects(author__in=authors)
    else:
        quotes = Quote.objects(tags__iregex=pattern)

    return serialize_quotes(quotes)


def get_cached_quotes(cache, operation, value):
    cache_key = f"quotes:{operation}:{value.casefold()}"
    cached_quotes = cache.get(cache_key)
    if cached_quotes is not None:
        return json.loads(cached_quotes)

    quotes = find_quotes(operation, value)
    cache.set(
        cache_key,
        json.dumps(quotes, ensure_ascii=False),
        ex=CACHE_TTL_SECONDS,
    )
    return quotes


def display_quotes(quotes):
    if not quotes:
        print("Цитат не знайдено.")
        return

    for quote in quotes:
        print(f"{quote['quote']} — {quote['author']}")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    connect_to_database()
    cache = create_cache_client()

    while True:
        command = input("Введіть команду: ").strip()
        if command.lower() == "exit":
            break

        operation, separator, value = command.partition(":")
        operation = operation.strip().lower()
        value = value.strip()
        if not separator or not value:
            print("Формат: name:ім'я, tag:тег, tags:тег1,тег2 або exit.")
            continue

        if operation in ("name", "tag"):
            display_quotes(get_cached_quotes(cache, operation, value))
        elif operation == "tags":
            tags = [tag.strip() for tag in value.split(",") if tag.strip()]
            if not tags:
                print("Вкажіть хоча б один тег.")
            else:
                display_quotes(serialize_quotes(Quote.objects(tags__in=tags)))
        else:
            print("Невідома команда. Використайте name:, tag:, tags: або exit.")


if __name__ == "__main__":
    main()
