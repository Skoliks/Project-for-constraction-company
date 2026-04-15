from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin
import re
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

PETROVICH_CATEGORY_URLS = {
    "Брус": "https://petrovich.ru/catalog/1293/obreznoy-brus/?ysclid=mnzil1o8ax639158481&sort=popularity_desc",
    "Доска обрезная": "https://petrovich.ru/catalog/783/strogannaya-obreznaya-doska/?ysclid=mnzibt1g3c572169868&sort=popularity_desc",
    "Минеральная вата": "https://rf.petrovich.ru/catalog/95761878/",
    "OSB-плита": "https://rf.petrovich.ru/catalog/778/",
    "Пенополистирол": "https://rf.petrovich.ru/catalog/1287/",
    "Цемент": "https://petrovich.ru/catalog/12111/?ysclid=mnzi9xmmgj712830783",
    "Арматура": "https://rf.petrovich.ru/catalog/12107/",
    "Металлочерепица": "https://petrovich.ru/catalog/1293/obreznoy-brus/?ysclid=mnzil1o8ax639158481&sort=popularity_desc",
    "Пластиковые окна": "https://rf.petrovich.ru/catalog/15635/",
    "Профнастил": "https://petrovich.ru/catalog/1526/?ysclid=mnzi8akqxy127700532",
}

BASE_URL = "https://petrovich.ru"

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


def get_main_page_with_playwright(url: str, wait_seconds: int = 10) -> str | None:
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=False,
                slow_mo=300,
            )

            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/126.0.0.0 Safari/537.36"
                ),
                locale="ru-RU",
                viewport={"width": 1440, "height": 900},
            )

            page = context.new_page()

            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(wait_seconds * 1000)

            html = page.content()

            browser.close()
            print("Страница успешно загружена через Playwright!")
            return html

    except PlaywrightTimeoutError as e:
        print("Timeout:", e)
        return None
    except Exception as e:
        print("Error:", e)
        return None


def _clean_price(value: str | None) -> str | None:
    if not value:
        return None

    # Убираем всё, кроме цифр
    digits = re.sub(r"[^\d]", "", value)
    return digits or None


def _extract_unit_from_card(card: BeautifulSoup) -> str | None:
    """
    Пытаемся достать единицу измерения из правого блока цены.
    По скринам это обычно: шт / упак / рул / м³.
    """
    card_text = card.get_text(" ", strip=True)

    if "Цена за" not in card_text:
        return None

    # Порядок важен: сначала более специфичные варианты
    known_units = ["упак", "шт", "рул", "м³", "м3"]

    for unit in known_units:
        if unit in card_text:
            return "м³" if unit == "м3" else unit

    return None


def _extract_price_per_base_unit(card: BeautifulSoup, price_rub: str | None) -> str | None:
    """
    На карточке есть подсказки вида:
    - 1 шт = 0.06м³
    - 1 упак = 0.288м³
    - 1 рул = 1м³

    Если удалось найти коэффициент и есть основная цена,
    считаем цену за м³.
    Если не хочешь пока считать, можешь просто вернуть None.
    """
    if not price_rub:
        return None

    card_text = card.get_text(" ", strip=True)
    normalized = card_text.replace(",", ".")

    match = re.search(r"1\s*(шт|упак|рул)\s*=\s*([0-9]+(?:\.[0-9]+)?)\s*(м³|м3)", normalized)
    if not match:
        return None

    try:
        factor = float(match.group(2))
        if factor <= 0:
            return None

        base_price = round(int(price_rub) / factor, 2)

        # Если цена целая, отдаем без .0
        if base_price.is_integer():
            return str(int(base_price))
        return str(base_price)
    except (ValueError, ZeroDivisionError):
        return None


def _extract_attributes(card: BeautifulSoup) -> dict | None:
    """
    Парсим блок product-description в словарь:
    Тип товара: Брус
    Тип: Естественной влажности
    ...
    """
    desc_block = card.find(attrs={"data-test": "product-description"})
    if not desc_block:
        return None

    attributes: dict[str, str] = {}

    # Разбиваем по <br>, потому что по скринам структура именно такая
    raw_html = str(desc_block)
    parts = re.split(r"<br\s*/?>", raw_html, flags=re.IGNORECASE)

    for part in parts:
        part_soup = BeautifulSoup(part, "html.parser")
        text = part_soup.get_text(" ", strip=True)

        if not text or ":" not in text:
            continue

        key, value = text.split(":", 1)
        key = key.strip()
        value = value.strip()

        if key and value:
            attributes[key] = value

    return attributes or None


def parse_petrovich_page(html: str, page_url: str) -> tuple[list[dict], list[str]]:
    soup = BeautifulSoup(html, "html.parser")
    data: list[dict] = []

    # Корневые карточки товаров
    cards = soup.select('div[data-item-code][data-item-page]')

    print(f"Найдено карточек товара: {len(cards)}")

    for card in cards:
        sku = card.get("data-item-code")

        # Ссылка
        product_url = None
        link_tag = card.find("a", attrs={"data-test": "product-link"}, href=True)
        if link_tag:
            product_url = urljoin(BASE_URL, link_tag["href"])

        # Название
        external_name = None
        title_tag = card.find(attrs={"data-test": "product-title"})
        if title_tag:
            external_name = title_tag.get_text(" ", strip=True)

        if not external_name:
            continue

        # Наличие
        stock_status = None
        remains_block = card.find(attrs={"data-test": "remains"})
        if remains_block:
            stock_status = remains_block.get("data-availability")

        # Текущая цена
        price_rub = None
        gold_price_tag = card.find(attrs={"data-test": "product-gold-price"})
        if gold_price_tag:
            price_rub = _clean_price(gold_price_tag.get_text(" ", strip=True))

        # Старая цена
        old_price_rub = None
        old_price_tag = card.find(attrs={"data-test": "product-retail-price"})
        if old_price_tag:
            old_price_rub = _clean_price(old_price_tag.get_text(" ", strip=True))

        # Единица измерения
        unit = _extract_unit_from_card(card)

        # Доп. атрибуты
        attributes_json = _extract_attributes(card)

        # Цена за базовую единицу, если получилось вычислить
        price_per_base_unit_rub = _extract_price_per_base_unit(card, price_rub)

        parsed_data = {
            "external_name": external_name.strip(),
            "product_url": product_url,
            "sku": sku,
            "unit": unit,
            "attributes_json": attributes_json,
            "price_rub": price_rub.strip() if isinstance(price_rub, str) else price_rub,
            "old_price_rub": old_price_rub,
            "price_per_base_unit_rub": price_per_base_unit_rub,
            "stock_status": stock_status,
        }

        data.append(parsed_data)

    # -----------------------------
    # Пагинация
    # -----------------------------
    pagination_urls: list[str] = []

    # По скринам ссылки страниц имеют data-test="paginator-page-btn"
    page_link_tags = soup.find_all("a", attrs={"data-test": "paginator-page-btn"}, href=True)

    for tag in page_link_tags:
        href = tag.get("href")
        if not href:
            continue

        full_url = urljoin(BASE_URL, href)
        if full_url != page_url and full_url not in pagination_urls:
            pagination_urls.append(full_url)

    print(f"Найдено ссылок пагинации: {len(pagination_urls)}")

    return data, pagination_urls





if __name__ == "__main__":
    url = PETROVICH_CATEGORY_URLS["Пластиковые окна"]

    html_page = get_main_page_with_playwright(url=url, wait_seconds=8)

    if html_page is None:
        print("HTML не получен")
    else:
        print("data-item-code:", "data-item-code" in html_page)
        print("product-title:", "product-title" in html_page)
        print("product-link:", "product-link" in html_page)

        items, pagination_urls = parse_petrovich_page(
            html=html_page,
            page_url=url,
        )

        print("Товаров найдено:", len(items))
        print("Ссылки пагинации:", pagination_urls)
        print(items[:3])
    