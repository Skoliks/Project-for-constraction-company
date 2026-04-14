from bs4 import BeautifulSoup
import requests


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
        response = requests.get(url=url, headers=headers,timeout=10)
        response.raise_for_status()
    except requests.exceptions.Timeout as e:
        print("Timeout:", e)
        return None
    except requests.exceptions.RequestException as e:
        print("Error:", e)
        return None
    
    print("Данные успешно загружены!")
    return response.text
    
    

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
                product_url = BASE_URL + href

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
            # Для supplier_products
            "external_name": external_name.strip(),
            "product_url": product_url,
            "sku": sku,
            "unit": unit,
            "attributes_json": None,

            # Для material_prices
            "price_rub": price_rub.strip(),
            "old_price_rub": old_price_rub,
            "price_per_base_unit_rub": None,
            "stock_status": None,
        }

        data.append(parsed_data)

    return data



def collect_page() -> list[dict]:
    pass


html = get_page(STROYLANDIYA_CATEGORY_URLS["Брус"])
print(parse_page(html=html))
