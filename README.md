# Scraping quotes

У проєкті є два скрипти для збору цитат і даних про авторів із
[quotes.toscrape.com](https://quotes.toscrape.com/):

- `scrape_quotes.py` — використовує Requests і BeautifulSoup.
- `scrapy_scraper/main.py` — використовує Scrapy.

Для запуску потрібен Python 3.10 або новіший та доступ до інтернету.
Команди нижче потрібно виконувати з кореневої директорії проєкту.

## Підготовка

Створіть і активуйте віртуальне середовище:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

У Windows PowerShell команда активації така:

```powershell
.venv\Scripts\Activate.ps1
```

## BeautifulSoup

Встановіть залежності та запустіть скрипт:

```bash
python -m pip install -r requirements.txt
python scrape_quotes.py
```

## Scrapy

Встановіть залежності Scrapy та запустіть скрипт:

```bash
python -m pip install -r scrapy_scraper/requirements.txt
python scrapy_scraper/main.py
```

Щоб зберегти результати в іншій директорії, передайте `--output-dir`:

```bash
python scrapy_scraper/main.py --output-dir ./data
```

Обидва скрипти створюють або перезаписують `quotes.json` і `authors.json`.
За замовчуванням файли зберігаються в корені проєкту.
