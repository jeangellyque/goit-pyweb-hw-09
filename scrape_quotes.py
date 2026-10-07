import json
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


START_URL = "http://quotes.toscrape.com/"
REQUEST_DELAY_SECONDS = 0.1


def fetch_soup(session, url):
    time.sleep(REQUEST_DELAY_SECONDS)
    response = session.get(url, timeout=20)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser"), response.url


def scrape_author(session, author_name, author_url):
    soup, _ = fetch_soup(session, author_url)
    selectors = {
        "born_date": ".author-born-date",
        "born_location": ".author-born-location",
        "description": ".author-description",
    }
    author = {"fullname": author_name}
    for field, selector in selectors.items():
        element = soup.select_one(selector)
        if element is None:
            raise ValueError(f"Missing {field} for author {author_name!r}")
        author[field] = element.get_text(" ", strip=True)
    return author


def scrape_site():
    session = requests.Session()
    session.headers.update(
        {"User-Agent": "Mozilla/5.0 (compatible; QuotesScraper/1.0)"}
    )
    page_url = START_URL
    visited_pages = set()
    quotes = []
    authors = {}

    while page_url and page_url not in visited_pages:
        visited_pages.add(page_url)
        soup, current_url = fetch_soup(session, page_url)
        quote_cards = soup.select(".quote")
        if not quote_cards:
            raise ValueError(f"No quotes found on {current_url}")

        for card in quote_cards:
            text = card.select_one(".text")
            author_element = card.select_one(".author")
            author_link = card.select_one('a[href^="/author/"]')
            if text is None or author_element is None or author_link is None:
                raise ValueError(f"Incomplete quote card on {current_url}")

            author_name = author_element.get_text(" ", strip=True)
            author_url = urljoin(current_url, author_link["href"])
            if author_name not in authors:
                authors[author_name] = scrape_author(
                    session,
                    author_name,
                    author_url,
                )

            quotes.append(
                {
                    "tags": [
                        tag.get_text(" ", strip=True)
                        for tag in card.select(".tags a.tag")
                    ],
                    "author": author_name,
                    "quote": text.get_text(" ", strip=True),
                }
            )

        next_link = soup.select_one("li.next a")
        page_url = (
            urljoin(current_url, next_link["href"])
            if next_link is not None
            else None
        )

    if not quotes or not authors:
        raise ValueError("The scrape returned no quotes or authors.")
    return quotes, list(authors.values())


def main():
    quotes, authors = scrape_site()
    project_dir = Path(__file__).resolve().parent
    (project_dir / "quotes.json").write_text(
        json.dumps(quotes, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (project_dir / "authors.json").write_text(
        json.dumps(authors, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Scraped {len(quotes)} quotes and {len(authors)} authors.")


if __name__ == "__main__":
    main()
