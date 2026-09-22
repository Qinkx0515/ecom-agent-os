import random
from datetime import (
    date,
    datetime,
    time,
    timedelta,
    timezone,
)
from decimal import Decimal

from sqlalchemy import select

from ecom_agent_os.database.models import (
    Order,
    OrderItem,
    Product,
    Refund,
    TrafficDaily,
    User,
)
from ecom_agent_os.database.session import SessionLocal


random.seed(42)


NUM_USERS = 500
PRODUCTS_PER_CATEGORY = 20
NUM_DAYS = 120


CATEGORIES = [
    "耳机",
    "键盘",
    "鼠标",
    "显示器",
    "充电器",
]


CATEGORY_PRICE_RANGE = {
    "耳机": (99, 699),
    "键盘": (129, 899),
    "鼠标": (59, 599),
    "显示器": (699, 2999),
    "充电器": (49, 299),
}


def create_users(session):

    users = []

    now = datetime.now(timezone.utc)

    for i in range(1, NUM_USERS + 1):

        user = User(
            email=f"user{i}@example.com",
            created_at=now,
        )

        session.add(user)
        users.append(user)

    session.flush()

    return users


def create_products(session):

    products = []

    product_index = 1

    for category in CATEGORIES:

        low_price, high_price = (
            CATEGORY_PRICE_RANGE[category]
        )

        for i in range(
            1,
            PRODUCTS_PER_CATEGORY + 1,
        ):

            price = Decimal(
                str(
                    round(
                        random.uniform(
                            low_price,
                            high_price,
                        ),
                        2,
                    )
                )
            )

            cost_ratio = random.uniform(
                0.45,
                0.72,
            )

            cost = Decimal(
                str(
                    round(
                        float(price) * cost_ratio,
                        2,
                    )
                )
            )

            product = Product(
                sku=f"SKU-{product_index:04d}",
                name=f"{category}-{i:02d}",
                category=category,
                price=price,
                cost=cost,
                stock=random.randint(
                    20,
                    500,
                ),
            )

            session.add(product)
            products.append(product)

            product_index += 1

    session.flush()

    return products


def get_business_multiplier(
    category: str,
    current_date: date,
    end_date: date,
):

    days_from_end = (
        end_date - current_date
    ).days

    traffic_multiplier = 1.0
    conversion_multiplier = 1.0
    refund_probability = 0.04

    if (
        category == "耳机"
        and days_from_end < 30
    ):
        traffic_multiplier = 0.80
        conversion_multiplier = 0.78
        refund_probability = 0.10

    return (
        traffic_multiplier,
        conversion_multiplier,
        refund_probability,
    )


def create_business_data(
    session,
    users,
    products,
):

    end_date = date.today()

    start_date = (
        end_date
        - timedelta(days=NUM_DAYS - 1)
    )

    order_count = 0
    refund_count = 0
    traffic_count = 0

    for day_offset in range(NUM_DAYS):

        current_date = (
            start_date
            + timedelta(days=day_offset)
        )

        for product in products:

            (
                traffic_multiplier,
                conversion_multiplier,
                refund_probability,
            ) = get_business_multiplier(
                product.category,
                current_date,
                end_date,
            )

            base_visitors = random.randint(
                12,
                55,
            )

            visitors = max(
                1,
                int(
                    base_visitors
                    * traffic_multiplier
                ),
            )

            impressions = int(
                visitors
                * random.uniform(
                    2.0,
                    4.5,
                )
            )

            base_conversion_rate = (
                random.uniform(
                    0.012,
                    0.035,
                )
            )

            conversion_rate = (
                base_conversion_rate
                * conversion_multiplier
            )

            conversions = max(
                0,
                round(
                    visitors
                    * conversion_rate
                ),
            )

            add_to_cart = max(
                conversions,
                round(
                    visitors
                    * random.uniform(
                        0.05,
                        0.12,
                    )
                ),
            )

            traffic = TrafficDaily(
                date=current_date,
                product_id=product.id,
                impressions=impressions,
                visitors=visitors,
                add_to_cart=add_to_cart,
                conversions=conversions,
            )

            session.add(traffic)

            traffic_count += 1

            for _ in range(conversions):

                user = random.choice(users)

                quantity = random.choices(
                    [1, 2],
                    weights=[0.92, 0.08],
                    k=1,
                )[0]

                unit_price = product.price

                total_amount = (
                    unit_price
                    * quantity
                )

                order_datetime = datetime.combine(
                    current_date,
                    time(
                        hour=random.randint(
                            8,
                            22,
                        ),
                        minute=random.randint(
                            0,
                            59,
                        ),
                    ),
                    tzinfo=timezone.utc,
                )

                order = Order(
                    user_id=user.id,
                    order_date=order_datetime,
                    status="completed",
                    total_amount=total_amount,
                )

                session.add(order)
                session.flush()

                item = OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=quantity,
                    unit_price=unit_price,
                )

                session.add(item)
                session.flush()

                order_count += 1

                if (
                    random.random()
                    < refund_probability
                ):

                    refund_created = (
                        order_datetime
                        + timedelta(
                            days=random.randint(
                                1,
                                7,
                            )
                        )
                    )

                    if (
                        refund_created
                        <= datetime.now(
                            timezone.utc
                        )
                    ):

                        refund = Refund(
                            order_item_id=item.id,
                            refund_amount=total_amount,
                            reason=random.choice(
                                [
                                    "质量问题",
                                    "不符合预期",
                                    "包装破损",
                                    "物流问题",
                                    "误购",
                                ]
                            ),
                            status="approved",
                            created_at=refund_created,
                        )

                        session.add(refund)

                        refund_count += 1

        if day_offset % 10 == 0:
            print(
                f"Generated day "
                f"{day_offset + 1}/"
                f"{NUM_DAYS}"
            )

    return {
        "orders": order_count,
        "refunds": refund_count,
        "traffic": traffic_count,
    }


def main():

    with SessionLocal() as session:

        existing_product = session.scalar(
            select(Product.id).limit(1)
        )

        if existing_product is not None:

            print(
                "Database already contains data."
            )

            print(
                "Seed cancelled to avoid "
                "duplicate records."
            )

            return

        print("Creating users...")

        users = create_users(
            session
        )

        print("Creating products...")

        products = create_products(
            session
        )

        print(
            "Creating traffic, orders "
            "and refunds..."
        )

        stats = create_business_data(
            session,
            users,
            products,
        )

        session.commit()

        print("\nSeed completed.")

        print(
            f"Users: {len(users)}"
        )

        print(
            f"Products: {len(products)}"
        )

        print(
            f"Traffic rows: "
            f"{stats['traffic']}"
        )

        print(
            f"Orders: {stats['orders']}"
        )

        print(
            f"Refunds: {stats['refunds']}"
        )


if __name__ == "__main__":
    main()