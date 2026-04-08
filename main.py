if __name__ == "__main__":
    query = "пальто из натуральной шерсти"

    # Парсим товары
    products = parse_products(query, max_pages=5)

    print(f"Всего товаров: {len(products)}")

    # Сохраняем полный каталог
    save_to_xlsx(products, "all_products.xlsx")

    # Применяем фильтр
    filtered = filter_products(products)

    # Сохраняем отфильтрованные товары
    save_to_xlsx(filtered, "filtered_products.xlsx")

    print("Готово!")
