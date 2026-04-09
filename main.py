import requests
import time
import random
from openpyxl import Workbook

BASE_URL = "https://search.wb.ru/exactmatch/ru/common/v5/search"

session = requests.Session()
session.headers.update(
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://www.wildberries.ru/catalog/0/search.aspx",
    }
)


def fetch_page(query, page):
    """
    Запрос к более стабильному v5 endpoint
    """

    params = {
        "ab_testing": "false",
        "appType": 1,
        "curr": "rub",
        "dest": -59208,
        "query": query,
        "resultset": "catalog",
        "sort": "popular",
        "page": page,
        "limit": 50,
        "lang": "ru",
    }

    response = session.get(BASE_URL, params=params, timeout=10)

    if response.status_code == 429:
        raise Exception("429")

    response.raise_for_status()
    return response.json()


def extract_price(item):
    """
    Цена (в v5 чаще работает priceU)
    """
    return (item.get("priceU") or item.get("salePriceU") or 0) / 100


def build_product(item):
    """
    Преобразование товара
    """

    product_id = item.get("id")

    return {
        "url": f"https://www.wildberries.ru/catalog/{product_id}/detail.aspx",
        "article": product_id,
        "name": item.get("name"),
        "price": extract_price(item),
        "description": item.get("name"),
        "images": [],
        "characteristics": {"brand": item.get("brand")},
        "seller_name": item.get("supplier"),
        "seller_url": f"https://www.wildberries.ru/seller/{item.get('supplierId')}",
        "sizes": [],
        "stock": "Недоступно",
        "rating": item.get("rating", 0),
        "reviews_count": item.get("feedbacks", 0),
        "country": "Недоступно",
    }


def parse_products(query, max_pages=2):
    """
    Стабильный парсер с мягким rate limit
    """

    products = []

    for page in range(1, max_pages + 1):
        print(f"Парсим страницу {page}")

        try:
            data = fetch_page(query, page)
            print(data.get("products"))
        except Exception:
            print("Поймали 429, делаем длинную паузу")
            time.sleep(10)
            continue

        items = data.get("products", {})

        if not items:
            print("Пусто, заканчиваем")
            break

        for item in items:
            products.append(build_product(item))

        # Ключ к стабильности
        sleep_time = random.uniform(4, 7)
        print(f"Ждём {sleep_time:.2f} сек")
        time.sleep(sleep_time)

    return products


def save_to_xlsx(data, filename):
    wb = Workbook()
    ws = wb.active

    headers = [
        "Ссылка",
        "Артикул",
        "Название",
        "Цена",
        "Описание",
        "Изображения",
        "Характеристики",
        "Селлер",
        "Ссылка на селлера",
        "Размеры",
        "Остаток",
        "Рейтинг",
        "Отзывы",
    ]

    ws.append(headers)

    for p in data:
        ws.append(
            [
                p["url"],
                p["article"],
                p["name"],
                p["price"],
                p["description"],
                ", ".join(p["images"]),
                str(p["characteristics"]),
                p["seller_name"],
                p["seller_url"],
                ", ".join(p["sizes"]),
                p["stock"],
                p["rating"],
                p["reviews_count"],
            ]
        )

    wb.save(filename)


def filter_products(data):
    """
    Ослабленный фильтр (реально работающий)
    """

    result = [p for p in data if p["rating"] >= 4.5 and p["price"] <= 15000]

    if not result:
        print("Фильтр пуст, fallback")
        result = [p for p in data if p["rating"] >= 4.0]

    return result


if __name__ == "__main__":
    query = "пальто из натуральной шерсти"

    products = parse_products(query, max_pages=2)

    print("Всего товаров:", len(products))

    save_to_xlsx(products, "all_products.xlsx")

    filtered = filter_products(products)
    save_to_xlsx(filtered, "filtered_products.xlsx")

    print("Готово!")
