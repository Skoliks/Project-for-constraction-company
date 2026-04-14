from decimal import Decimal, InvalidOperation
from sqlalchemy.orm import Session

from app.parsers.stroylandia_parser import collect_page
from app.repositories.supplier_repository import supplier_repository
from app.repositories.material_repository import material_repository
from app.repositories.supplier_product_repository import supplier_product_repository
from app.repositories.material_price_repository import material_price_repository
from app.schemas.supplier_product_schema import CreateSupplierProduct
from app.schemas.material_price_schema import CreateMaterialPrice


class StroylandiyaImportService:
    async def run_import(self, db: Session) -> dict:
        parsed_items = await collect_page()

        supplier = supplier_repository.get_by_url(
            db=db,
            url="https://stroylandiya.ru"
        )
        if supplier is None:
            raise ValueError("Supplier 'Стройландия' not found in database")

        created_supplier_products = 0
        reused_supplier_products = 0
        created_material_prices = 0
        skipped_items = 0

        for item in parsed_items:
            material_name = item.get("material_name")
            if not material_name:
                skipped_items += 1
                continue

            material = material_repository.get_by_name(db=db, name=material_name)
            if material is None:
                skipped_items += 1
                continue

            product_url = item.get("product_url")
            if not product_url:
                skipped_items += 1
                continue

            supplier_product = supplier_product_repository.get_by_product_url(
                db=db,
                product_url=product_url
            )

            if supplier_product is None:
                supplier_product_data = CreateSupplierProduct(
                    supplier_id=supplier.id,
                    material_id=material.id,
                    external_name=item.get("external_name"),
                    product_url=product_url,
                    sku=item.get("sku"),
                    unit=item.get("unit"),
                    attributes_json=item.get("attributes_json"),
                )
                supplier_product = supplier_product_repository.create(
                    db=db,
                    new_data=supplier_product_data
                )
                created_supplier_products += 1
            else:
                reused_supplier_products += 1

            price_rub = self._to_decimal(item.get("price_rub"))
            old_price_rub = self._to_decimal(item.get("old_price_rub"))
            price_per_base_unit_rub = self._to_decimal(item.get("price_per_base_unit_rub"))

            if price_rub is None:
                skipped_items += 1
                continue

            material_price_data = CreateMaterialPrice(
                supplier_product_id=supplier_product.id,
                price_rub=price_rub,
                old_price_rub=old_price_rub,
                price_per_base_unit_rub=price_per_base_unit_rub,
                stock_status=item.get("stock_status"),
            )

            material_price_repository.create(db=db, new_data=material_price_data)
            created_material_prices += 1

        return {
            "source": "stroylandiya",
            "parsed_items": len(parsed_items),
            "created_supplier_products": created_supplier_products,
            "reused_supplier_products": reused_supplier_products,
            "created_material_prices": created_material_prices,
            "skipped_items": skipped_items,
        }

    @staticmethod
    def _to_decimal(value) -> Decimal | None:
        if value is None:
            return None

        if isinstance(value, Decimal):
            return value

        value_str = str(value).strip().replace(" ", "").replace(",", ".")
        if not value_str:
            return None

        try:
            return Decimal(value_str)
        except (InvalidOperation, ValueError):
            return None


stroylandiya_import_service = StroylandiyaImportService()