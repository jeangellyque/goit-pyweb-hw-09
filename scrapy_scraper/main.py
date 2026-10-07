import argparse
import json
from pathlib import Path
from urllib.parse import urljoin

import scrapy
from scrapy.crawler import CrawlerProcess


START_URL = "http://quotes.toscrape.com/"
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent.parent


class QuotesSpider(scrapy.Spider):
    name = "quotes"
    start_urls = [START_URL]
    custom_settings = {
        "CONCURRENT_REQUESTS": 8,
        "DOWNLOAD_DELAY": 0.1,
        "ROBOTSTXT_OBEY": True,
        "USER_AGENT": "QuotesScrapy/1.0 (+https://quotes.toscrape.com/)",
        "LOG_LEVEL": "INFO",
    }

    def __init__(self, output_dir=DEFAULT_OUTPUT_DIR, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.output_dir = Path(output_dir)
        self.quotes = []
        self.authors = {}
        self.requested_authors = set()

    def parse(self, response):
        quote_cards = response.css(".quote")
        if not quote_cards:
            self.logger.error("No quote cards found on %s", response.url)
            return

        for card in quote_cards:
            quote_text = card.css(".text::text").get()
            author_name = card.css(".author::text").get()
            author_path = card.css('a[href^="/author/"]::attr(href)').get()
            if not quote_text or not author_name or not author_path:
                self.logger.error("Incomplete quote card on %s", response.url)
                continue

            author_name = author_name.strip()
            self.quotes.append(
                {
                    "tags": [
                        tag.strip()
                        for tag in card.css(".tags a.tag::text").getall()
                    ],
                    "author": author_name,
                    "quote": quote_text.strip(),
                }
            )

            author_url = urljoin(response.url, author_path)
            if author_name not in self.requested_authors:
                self.requested_authors.add(author_name)
                yield scrapy.Request(
                    author_url,
                    callback=self.parse_author,
                    cb_kwargs={"author_name": author_name},
                )

        next_path = response.css("li.next a::attr(href)").get()
        if next_path:
            yield response.follow(next_path, callback=self.parse)

    def parse_author(self, response, author_name):
        fields = {
            "born_date": response.css(".author-born-date::text").get(),
            "born_location": response.css(".author-born-location::text").get(),
            "description": response.css(".author-description::text").get(),
        }
        if not all(fields.values()):
            self.logger.error("Incomplete author details for %s", author_name)
            return

        self.authors[author_name] = {
            "fullname": author_name,
            **{key: value.strip() for key, value in fields.items()},
        }

    def closed(self, reason):
        if not self.quotes or not self.authors:
            return

        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "quotes.json").write_text(
            json.dumps(self.quotes, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (self.output_dir / "authors.json").write_text(
            json.dumps(list(self.authors.values()), ensure_ascii=False, indent=2)
            + "\n",
            encoding="utf-8",
        )


def main():
    parser = argparse.ArgumentParser(
        description="Scrape quotes and authors using Scrapy."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="directory for quotes.json and authors.json (defaults to the parent project)",
    )
    args = parser.parse_args()

    process = CrawlerProcess()
    crawler = process.create_crawler(QuotesSpider)
    process.crawl(crawler, output_dir=args.output_dir.resolve())
    process.start()

    spider = crawler.spider
    if spider is None or not spider.quotes or not spider.authors:
        raise RuntimeError("Scrapy did not collect quotes and author records.")

    missing_authors = {
        quote["author"] for quote in spider.quotes
    } - spider.authors.keys()
    if missing_authors:
        raise RuntimeError(
            f"Author pages could not be scraped: {', '.join(sorted(missing_authors))}"
        )

    print(
        f"Scraped {len(spider.quotes)} quotes and {len(spider.authors)} authors "
        f"to {args.output_dir.resolve()}."
    )


if __name__ == "__main__":
    main()
