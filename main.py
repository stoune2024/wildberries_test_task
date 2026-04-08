import requests
import time

# Целевой URL из WB API
BASE_URL = "https://search.wb.ru/exactmatch/ru/common/v4/search"

# Заголовки во избежание блокировки
HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "*/*"}


def fetch_page(query, page):
    """
    Делает один запрос к API Wildberries и возвращает JSON с товарами.

    :param query: поисковый запрос (например, "пальто из натуральной шерсти")
    :param page: номер страницы
    :return: dict (распарсенный JSON)
    """
    try:
        # Параметры запроса (взяты из реального запроса сайта)
        params = {
            "appType": 1,
            "curr": "rub",
            "dest": -1257786,  # регион (можно менять)
            "query": query,
            "resultset": "catalog",
            "sort": "popular",
            "page": page,
        }

        # Выполняем GET-запрос
        response = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=10)

        # Если статус не 200 → выбросит исключение
        response.raise_for_status()

        return response.json()
    except Exception as e:
        print(f"Ошибка запроса к API Wildberries: {e}")


def build_product(item):
    """
    Преобразует один товар из формата WB API в нужную нам структуру.

    :param item: dict (один товар из API)
    :return: dict (нормализованный товар)
    """
    try:
        product_id = item.get("id")
        root = item.get("root")

        # Формируем ссылку на товар
        url = f"https://www.wildberries.ru/catalog/{product_id}/detail.aspx"

        # Цена приходит в копейках → переводим в рубли
        price = item.get("salePriceU", 0) / 100

        # Рейтинг и отзывы
        rating = item.get("rating", 0)
        feedbacks = item.get("feedbacks", 0)

        sizes = []
        stock = 0

        # Проходим по размерам и считаем остатки
        for size in item.get("sizes", []):
            if "name" in size:
                sizes.append(size["name"])

            # Внутри каждого размера есть склады (stocks)
            for stock_item in size.get("stocks", []):
                stock += stock_item.get("qty", 0)

        # Генерация ссылок на изображения (по шаблону WB)
        images = [
            f"https://images.wbstatic.net/c246x328/{root}/images/big/{product_id}-{i}.jpg"
            for i in range(1, 4)
        ]

        # Собираем итоговую структуру
        product = {
            "url": url,
            "article": product_id,
            "name": item.get("name"),
            "price": price,
            # В поисковом API нет описания → используем название как заглушку
            "description": item.get("name"),
            "images": images,
            # Характеристики (в урезанном виде)
            "characteristics": {
                "brand": item.get("brand"),
                "supplier": item.get("supplier"),
            },
            "seller_name": item.get("supplier"),
            "seller_url": f"https://www.wildberries.ru/seller/{item.get('supplierId')}",
            "sizes": sizes,
            "stock": stock,
            "rating": rating,
            "reviews_count": feedbacks,
            # Не всегда приходит → оставляем fallback
            "country": item.get("country", "Не указано"),
        }

        return product
    except Exception as e:
        print(f"Ошибка при попытке преобразования: {e}")


def parse_products(query, max_pages=3):
    """
    Основная функция парсинга.

    Проходит по страницам поиска и собирает список товаров.

    :param query: поисковый запрос
    :param max_pages: сколько страниц парсить
    :return: list словарей с товарами
    """
    try:
        products = []

        # Идём по страницам поиска
        for page in range(1, max_pages + 1):
            print(f"Парсим страницу {page}...")

            data = fetch_page(query, page)

            # Достаём список товаров из JSON
            items = data.get("data", {}).get("products", [])

            # Если товаров нет — дальше идти нет смысла
            if not items:
                break

            for item in items:
                # Преобразуем сырой JSON в удобную структуру
                product = build_product(item)
                products.append(product)

            # Небольшая пауза, чтобы снизить шанс блокировки и обойти rate limitter
            time.sleep(1)

        return products
    except Exception as e:
        print(f"Ошибка при попытке парсинга: {e}")


# if __name__ == "__main__":
#     query = "пальто из натуральной шерсти"
#
#     # Парсим товары
#     products = parse_products(query, max_pages=5)
#
#     print(f"Всего товаров: {len(products)}")
#
#     # Сохраняем полный каталог
#     save_to_xlsx(products, "all_products.xlsx")
#
#     # Применяем фильтр
#     filtered = filter_products(products)
#
#     # Сохраняем отфильтрованные товары
#     save_to_xlsx(filtered, "filtered_products.xlsx")
#
#     print("Готово!")
