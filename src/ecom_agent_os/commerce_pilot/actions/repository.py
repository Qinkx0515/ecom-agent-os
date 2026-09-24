from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import select

from ecom_agent_os.database.models import (
    Product,
)
from ecom_agent_os.database.session import (
    SessionLocal,
)


@dataclass
class ProductSnapshot:

    id: int

    sku: str

    name: str

    category: str

    price: Decimal

    stock: int


@dataclass
class PriceUpdateResult:

    sku: str

    old_price: Decimal

    new_price: Decimal

    status: str


class ActionExecutionError(
    RuntimeError
):
    pass


def get_product_snapshot(
    sku: str,
) -> ProductSnapshot | None:

    with SessionLocal() as session:

        product = session.scalar(
            select(Product)
            .where(
                Product.sku
                == sku
            )
        )

        if product is None:
            return None

        return ProductSnapshot(
            id=product.id,
            sku=product.sku,
            name=product.name,
            category=product.category,
            price=product.price,
            stock=product.stock,
        )


def update_product_price(
    sku: str,
    new_price: Decimal,
    expected_old_price: Decimal,
) -> PriceUpdateResult:

    with SessionLocal() as session:

        product = session.scalar(
            select(Product)
            .where(
                Product.sku
                == sku
            )
            .with_for_update()
        )

        if product is None:

            raise ActionExecutionError(
                f"Product not found: "
                f"{sku}"
            )


        current_price = (
            product.price
        )


        # ===== Idempotency =====

        if (
            current_price
            == new_price
        ):

            return PriceUpdateResult(
                sku=sku,
                old_price=current_price,
                new_price=new_price,
                status="already_applied",
            )


        # ===== Optimistic Safety =====

        if (
            current_price
            != expected_old_price
        ):

            raise ActionExecutionError(
                "Product price changed "
                "after approval request. "
                f"Expected: "
                f"{expected_old_price}, "
                f"Current: "
                f"{current_price}"
            )


        product.price = (
            new_price
        )

        session.commit()


        return PriceUpdateResult(
            sku=sku,
            old_price=current_price,
            new_price=new_price,
            status="updated",
        )