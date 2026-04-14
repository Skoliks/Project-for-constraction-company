from bs4 import BeautifulSoup
import requests
import time
import math
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse


STROYLANDIYA_CATEGORY_URLS = {
    "Брус": "https://stroylandiya.ru/catalog/brus/",
    "Доска обрезная": "https://stroylandiya.ru/catalog/doska/",
    "Минеральная вата": "https://stroylandiya.ru/search/?q=минеральная%20вата",
    "OSB - плита": "https://stroylandiya.ru/catalog/osb-plity/",
    "Пенополистирол": "https://stroylandiya.ru/catalog/penopolistirolnye-plity/",
    "Цемент": "https://stroylandiya.ru/catalog/tsement/",
    "Арматура": "https://stroylandiya.ru/catalog/armatura/",
    "Пластиковые окна": "https://stroylandiya.ru/catalog/plastikovie-okna/",
    "Профнастил": "https://stroylandiya.ru/search/?q=профнастил"
}

BASE_URL = "https://stroylandiya.ru"

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "keep-alive",
}


def get_page(url: str) -> str | None:
    try:
        response = requests.get(url=url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.exceptions.Timeout as e:
        print("Timeout:", e)
        return None
    except requests.exceptions.RequestException as e:
        print("Error:", e)
        return None

    print(f"Данные успешно загружены: {url}")
    return response.text


def get_total_pages(html: str) -> int:
    """
    Определяем число страниц категории.

    Приоритет:
    1. Через data-total и data-per-page из блока .fb-pagination
    2. Через максимальный data-page у .fb-pagination__page
    3. Если пагинации нет - 1 страница
    """
    soup = BeautifulSoup(html, "html.parser")

    pagination = soup.find("div", class_="fb-pagination")
    if pagination is not None:
        total = pagination.get("data-total")
        per_page = pagination.get("data-per-page")

        if total and per_page:
            try:
                total = int(total)
                per_page = int(per_page)

                if per_page > 0:
                    total_pages = math.ceil(total / per_page)
                    return max(total_pages, 1)
            except ValueError:
                pass

    page_items = soup.find_all("li", class_="fb-pagination__page")
    page_numbers = []

    for item in page_items:
        data_page = item.get("data-page")
        if data_page and data_page.isdigit():
            page_numbers.append(int(data_page))

    if page_numbers:
        return max(page_numbers)

    return 1


def add_or_replace_query_param(url: str, key: str, value: str) -> str:
    """
    Добавляет или заменяет query-параметр в URL.
    Работает и для catalog, и для search.
    """
    parsed = urlparse(url)
    query = parse_qs(parsed.query, keep_blank_values=True)

    query[key] = [value]

    new_query = urlencode(query, doseq=True)
    new_url = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        new_query,
        parsed.fragment
    ))
    return new_url


def build_pagination_urls(category_url: str, html: str) -> list[str]:
    """
    Собирает список URL всех страниц категории.

    Логика:
    - первая страница = category_url
    - если в html есть прямые href в пагинации, берем их
    - если не хватает страниц, достраиваем вручную через PAGEN_1
    """
    soup = BeautifulSoup(html, "html.parser")
    total_pages = get_total_pages(html)

    page_urls = [category_url]

    if total_pages == 1:
        return page_urls

    # 1. Пытаемся взять реальные ссылки из пагинации
    pagination_links = soup.select("li.fb-pagination__page a[href]")
    found_urls = set()

    for a_tag in pagination_links:
        href = a_tag.get("href")
        if not href:
            continue

        full_url = urljoin(BASE_URL, href)
        found_urls.add(full_url)

    # добавляем найденные ссылки
    for url in found_urls:
        if url not in page_urls:
            page_urls.append(url)

    # 2. Если каких-то страниц не хватило — достраиваем сами
    # На сайте используется PAGEN_1=2
    for page_num in range(2, total_pages + 1):
        fallback_url = add_or_replace_query_param(category_url, "PAGEN_1", str(page_num))
        if fallback_url not in page_urls:
            page_urls.append(fallback_url)

    # сортировка по номеру страницы
    def get_page_num(url: str) -> int:
        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        values = query.get("PAGEN_1")
        if not values:
            return 1
        try:
            return int(values[0])
        except ValueError:
            return 1

    page_urls = sorted(set(page_urls), key=get_page_num)
    return page_urls


def parse_page(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    data = []

    cards = soup.find_all("div", class_="any-recs-product")

    print(f"Найдено {len(cards)} карточек товара")

    for card in cards:
        price_rub = card.get("data-price")
        external_name = card.get("data-name")
        sku = card.get("data-id")

        if price_rub is None or external_name is None:
            continue

        product_url = None
        link_tag = card.find("a", href=True)
        if link_tag is not None:
            href = link_tag.get("href")
            if href:
                product_url = urljoin(BASE_URL, href)

        unit = None
        price_text_block = card.find("div", class_="fb-product-card__price-value")
        if price_text_block is not None:
            price_text = price_text_block.get_text(strip=True)
            if "/" in price_text:
                unit = price_text.split("/")[-1].strip()

        old_price_rub = None
        old_price_block = card.find("div", class_="fb-product-card__price-old-value")
        if old_price_block is not None:
            old_price_text = old_price_block.get_text(strip=True)
            old_price_text = (
                old_price_text
                .replace("₽", "")
                .replace("Р", "")
                .replace("/шт", "")
                .replace(" ", "")
                .strip()
            )
            if old_price_text.isdigit():
                old_price_rub = old_price_text

        parsed_data = {
            "external_name": external_name.strip(),
            "product_url": product_url,
            "sku": sku,
            "unit": unit,
            "attributes_json": None,
            "price_rub": price_rub.strip(),
            "old_price_rub": old_price_rub,
            "price_per_base_unit_rub": None,
            "stock_status": None,
        }

        data.append(parsed_data)

    return data


def collect_page(delay_seconds: float = 2.0) -> list[dict]:
    all_data: list[dict] = []
    seen_skus: set[tuple[str, str]] = set()  # (material_name, sku)

    for material_name, category_url in STROYLANDIYA_CATEGORY_URLS.items():
        print(f"\n{'=' * 70}")
        print(f"Начинаю обработку категории: {material_name}")
        print(f"URL категории: {category_url}")

        first_html = get_page(category_url)
        if first_html is None:
            print(f"Не удалось получить первую страницу для категории: {material_name}")
            time.sleep(delay_seconds)
            continue

        page_urls = build_pagination_urls(category_url, first_html)
        print(f"Всего страниц в категории '{material_name}': {len(page_urls)}")

        category_count = 0

        for page_index, page_url in enumerate(page_urls, start=1):
            print(f"\nПарсим страницу {page_index}/{len(page_urls)}: {page_url}")

            if page_index == 1:
                html = first_html
            else:
                html = get_page(page_url)
                if html is None:
                    print(f"Не удалось получить страницу: {page_url}")
                    time.sleep(delay_seconds)
                    continue

            parsed_items = parse_page(html)

            unique_items = []
            for item in parsed_items:
                item["material_name"] = material_name
                item["source_url"] = page_url

                sku = item.get("sku")
                unique_key = (material_name, sku)

                # защита от дублей
                if sku is not None and unique_key in seen_skus:
                    continue

                if sku is not None:
                    seen_skus.add(unique_key)

                unique_items.append(item)

            all_data.extend(unique_items)
            category_count += len(unique_items)

            print(f"Собрано товаров с этой страницы: {len(unique_items)}")

            time.sleep(delay_seconds)

        print(f"\nИтого собрано по категории '{material_name}': {category_count}")

    print(f"\n{'=' * 70}")
    print(f"Всего собрано товаров: {len(all_data)}")
    return all_data


if __name__ == "__main__":
    data = collect_page(delay_seconds=1.0)
    print(f"Финальный результат: {len(data)} товаров")



