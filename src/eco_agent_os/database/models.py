from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    orders: Mapped[list["Order"]] = relationship(
        back_populates="user"
    )


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    sku: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    category: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )

    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    cost: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    stock: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    order_items: Mapped[list["OrderItem"]] = relationship(
        back_populates="product"
    )

    traffic_records: Mapped[list["TrafficDaily"]] = relationship(
        back_populates="product"
    )


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    order_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        back_populates="orders"
    )

    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order"
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id"),
        nullable=False,
        index=True,
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"),
        nullable=False,
        index=True,
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    order: Mapped["Order"] = relationship(
        back_populates="items"
    )

    product: Mapped["Product"] = relationship(
        back_populates="order_items"
    )

    refund: Mapped["Refund | None"] = relationship(
        back_populates="order_item",
        uselist=False,
    )


class TrafficDaily(Base):
    __tablename__ = "traffic_daily"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"),
        nullable=False,
    )

    impressions: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    visitors: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    add_to_cart: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    conversions: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    product: Mapped["Product"] = relationship(
        back_populates="traffic_records"
    )

    __table_args__ = (
        UniqueConstraint(
            "date",
            "product_id",
            name="uq_traffic_date_product",
        ),
        Index(
            "ix_traffic_product_date",
            "product_id",
            "date",
        ),
    )


class Refund(Base):
    __tablename__ = "refunds"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    order_item_id: Mapped[int] = mapped_column(
        ForeignKey("order_items.id"),
        unique=True,
        nullable=False,
    )

    refund_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    reason: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    order_item: Mapped["OrderItem"] = relationship(
        back_populates="refund"
    )