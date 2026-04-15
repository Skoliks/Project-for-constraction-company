import asyncio
import math
from urllib.parse import parse_qs, urlencode, urljoin, urlparse, urlunparse

import aiohttp
from bs4 import BeautifulSoup

from app.core.logger import get_logger


STROYLANDIYA_CATEGORY_URLS = {
    "Брус": "https://stroylandiya.ru/catalog/brus/",
    "Доска обрезная": "https://stroylandiya.ru/catalog/doska/",
    "Минеральная вата": "https://stroylandiya.ru/search/?q=минеральная%20вата",
    "OSB-плита": "https://stroylandiya.ru/catalog/osb-plity/",
    "Пенополистирол": "https://stroylandiya.ru/catalog/penopolistirolnye-plity/",
    "Цемент": "https://stroylandiya.ru/catalog/tsement/",
    "Арматура": "https://stroylandiya.ru/catalog/armatura/",
    "Пластиковые окна": "https://stroylandiya.ru/catalog/plastikovie-okna/",
    "Профнастил": "https://stroylandiya.ru/search/?q=профнастил",
}

BASE_URL = "https://stroylandiya.ru"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "keep-alive",
}

MAX_CONCURRENT_REQUESTS = 3
REQUEST_DELAY_SECONDS = 0.5

logger = get_logger(__name__)


def get_total_pages(html: str) -> int:
    soup = BeautifulSoup(html, "lxml")

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
    parsed = urlparse(url)
    query = parse_qs(parsed.query, keep_blank_values=True)

    query[key] = [value]

    new_query = urlencode(query, doseq=True)
    new_url = urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            parsed.fragment,
        )
    )
    return new_url


def build_pagination_urls(category_url: str, html: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    total_pages = get_total_pages(html)

    page_urls = [category_url]

    if total_pages == 1:
        return page_urls

    pagination_links = soup.select("li.fb-pagination__page a[href]")
    found_urls = set()

    for a_tag in pagination_links:
        href = a_tag.get("href")
        if not href:
            continue

        full_url = urljoin(BASE_URL, href)
        found_urls.add(full_url)

    for url in found_urls:
        if url not in page_urls:
            page_urls.append(url)

    for page_num in range(2, total_pages + 1):
        fallback_url = add_or_replace_query_param(category_url, "PAGEN_1", str(page_num))
        if fallback_url not in page_urls:
            page_urls.append(fallback_url)

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

    return sorted(set(page_urls), key=get_page_num)


def parse_page(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    data = []

    cards = soup.find_all("div", class_="any-recs-product")
    logger.info("Найдено карточек товара: %s", len(cards))

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
                .replace("в‚Ѕ", "")
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


async def get_page(
    session: aiohttp.ClientSession,
    url: str,
    semaphore: asyncio.Semaphore,
    delay_seconds: float = REQUEST_DELAY_SECONDS,
) -> str | None:
    async with semaphore:
        if delay_seconds > 0:
            await asyncio.sleep(delay_seconds)

        try:
            async with session.get(url) as response:
                response.raise_for_status()
                html = await response.text()
                logger.info("Страница успешно загружена: %s", url)
                return html

        except asyncio.TimeoutError:
            logger.warning("Timeout при загрузке страницы: %s", url)
            return None
        except aiohttp.ClientResponseError as e:
            logger.warning("HTTP error %s при загрузке страницы: %s", e.status, url)
            return None
        except aiohttp.ClientError as e:
            logger.warning("Client error при загрузке страницы %s: %s", url, e)
            return None


async def fetch_and_parse_page(
    session: aiohttp.ClientSession,
    material_name: str,
    page_url: str,
    semaphore: asyncio.Semaphore,
) -> tuple[str, str, list[dict]]:
    html = await get_page(session, page_url, semaphore)
    if html is None:
        return material_name, page_url, []

    parsed_items = parse_page(html)

    for item in parsed_items:
        item["material_name"] = material_name
        item["source_url"] = page_url

    logger.info(
        "Собрано товаров со страницы | material=%s | url=%s | items=%s",
        material_name,
        page_url,
        len(parsed_items),
    )
    return material_name, page_url, parsed_items


async def collect_page() -> list[dict]:
    all_data: list[dict] = []
    seen_skus: set[tuple[str, str]] = set()
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

    timeout = aiohttp.ClientTimeout(total=20)
    connector = aiohttp.TCPConnector(limit=MAX_CONCURRENT_REQUESTS)

    async with aiohttp.ClientSession(
        headers=HEADERS,
        timeout=timeout,
        connector=connector,
    ) as session:
        for material_name, category_url in STROYLANDIYA_CATEGORY_URLS.items():
            logger.info(
                "Старт обработки категории | material=%s | url=%s",
                material_name,
                category_url,
            )

            first_html = await get_page(session, category_url, semaphore)
            if first_html is None:
                logger.warning(
                    "Не удалось получить первую страницу категории | material=%s | url=%s",
                    material_name,
                    category_url,
                )
                continue

            page_urls = build_pagination_urls(category_url, first_html)
            logger.info(
                "Определено страниц в категории | material=%s | pages=%s",
                material_name,
                len(page_urls),
            )

            category_results: list[tuple[str, str, list[dict]]] = []

            first_items = parse_page(first_html)
            for item in first_items:
                item["material_name"] = material_name
                item["source_url"] = category_url
            category_results.append((material_name, category_url, first_items))

            other_page_urls = page_urls[1:]
            tasks = [
                fetch_and_parse_page(session, material_name, page_url, semaphore)
                for page_url in other_page_urls
            ]

            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)

                for result in results:
                    if isinstance(result, Exception):
                        logger.exception(
                            "Ошибка при обработке страницы категории | material=%s | error=%s",
                            material_name,
                            result,
                        )
                        continue
                    category_results.append(result)

            category_count = 0

            for _, _, parsed_items in category_results:
                unique_items = []

                for item in parsed_items:
                    sku = item.get("sku")
                    unique_key = (material_name, sku)

                    if sku is not None and unique_key in seen_skus:
                        continue

                    if sku is not None:
                        seen_skus.add(unique_key)

                    unique_items.append(item)

                all_data.extend(unique_items)
                category_count += len(unique_items)

            logger.info(
                "Категория обработана | material=%s | unique_items=%s",
                material_name,
                category_count,
            )

    logger.info("Сбор Стройландии завершен | total_items=%s", len(all_data))
    return all_data


async def main() -> None:
    data = await collect_page()
    logger.info("Финальный результат парсера | total_items=%s", len(data))


if __name__ == "__main__":
    asyncio.run(main())
