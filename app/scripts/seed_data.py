from app.core.database import SessionLocal
from app.models.material import Material
from app.models.supplier import Supplier


MATERIALS = [
    {
        "name": "Брус",
        "category": "timber",
        "base_unit": "м3",
        "description": "Строительный брус",
    },
    {
        "name": "Доска обрезная",
        "category": "board",
        "base_unit": "м3",
        "description": "Обрезная доска",
    },
    {
        "name": "OSB-плита",
        "category": "osb",
        "base_unit": "лист",
        "description": "Ориентированно-стружечная плита",
    },
    {
        "name": "Минеральная вата",
        "category": "insulation",
        "base_unit": "м2",
        "description": "Теплоизоляционный материал",
    },
    {
        "name": "Пенополистирол",
        "category": "insulation",
        "base_unit": "м2",
        "description": "Плитный утеплитель",
    },
    {
        "name": "Бетон",
        "category": "concrete",
        "base_unit": "м3",
        "description": "Товарный бетон",
    },
    {
        "name": "Арматура",
        "category": "metal",
        "base_unit": "т",
        "description": "Арматурный металлопрокат",
    },
    {
        "name": "Металлочерепица",
        "category": "roofing",
        "base_unit": "м2",
        "description": "Кровельный материал",
    },
    {
        "name": "Пластиковые окна",
        "category": "windows",
        "base_unit": "шт",
        "description": "Окна ПВХ",
    },
    {
        "name": "Профнастил",
        "category": "roofing",
        "base_unit": "м2",
        "description": "Профилированный лист",
    },
]

SUPPLIERS = [
    {
        "name": "Стройландия",
        "city": "Оренбург",
        "website_url": "https://stroylandiya.ru",
        "description": "Сеть магазинов строительных материалов",
    },
    {
        "name": "Петрович",
        "city": "Санкт-Петербург",
        "website_url": "https://rf.petrovich.ru",
        "description": "Поставщик строительных материалов",
    },
    {
        "name": "Эко Газоблок",
        "city": "Южно-Сахалинск",
        "website_url": "https://agb65.ru",
        "description": "Поставщик газоблока",
    },
    {
        "name": "Лемана Про",
        "city": "Москва",
        "website_url": "https://lemanapro.ru",
        "description": "Сеть строительных и отделочных товаров",
    },
]


def seed_materials(db):
    for material_data in MATERIALS:
        existing_material = db.query(Material).filter(
            Material.name == material_data["name"]
        ).first()

        if existing_material is None:
            material = Material(**material_data)
            db.add(material)

    db.commit()


def seed_suppliers(db):
    for supplier_data in SUPPLIERS:
        existing_supplier = db.query(Supplier).filter(
            Supplier.website_url == supplier_data["website_url"]
        ).first()

        if existing_supplier is None:
            supplier = Supplier(**supplier_data)
            db.add(supplier)

    db.commit()


def run_seed():
    db = SessionLocal()
    try:
        seed_materials(db)
        seed_suppliers(db)
        print("Seed completed successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()