#
#  product_repository.py
#  hot_dog_chatbot
#
#  Created by Codex on 2026-05-10.
#
#  Codex Update Log:
#  - 2026-05-10: Added MySQL product lookup for Ollama-backed recommendations.
#

from __future__ import annotations

import re
from functools import lru_cache
from typing import Any

import pymysql
from pymysql.cursors import DictCursor

import config


PRODUCT_TABLE = "product"
MAX_RECOMMENDATIONS = 5
MAX_SEARCH_TERMS = 8
TEXT_COLUMN_TYPES = ("char", "text", "enum", "set", "json")
NUMBER_COLUMN_TYPES = ("int", "decimal", "float", "double", "real")
PREFERRED_TEXT_COLUMNS = (
    "name",
    "product_name",
    "title",
    "category",
    "brand",
    "description",
    "content",
    "detail",
    "size",
    "age",
    "breed",
    "ingredient",
    "material",
)
PREFERRED_OUTPUT_COLUMNS = (
    "id",
    "product_id",
    "name",
    "product_name",
    "title",
    "category",
    "category_name",
    "brand",
    "price",
    "sale_price",
    "discount_price",
    "stock",
    "quantity",
    "size",
    "age",
    "breed",
    "description",
    "content",
    "detail",
    "image_url",
    "thumbnail",
)
STOPWORDS = {
    "추천",
    "상품",
    "제품",
    "문의",
    "어떤",
    "있어",
    "있나요",
    "좋아",
    "좋나요",
    "주세요",
    "해줘",
    "알려줘",
    "강아지",
    "반려견",
    "애견",
}


class ProductRepositoryError(RuntimeError):
    pass


def _connect():
    try:
        return pymysql.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME,
            charset=getattr(config, "DB_CHARSET", "utf8mb4"),
            cursorclass=DictCursor,
            connect_timeout=5,
            read_timeout=10,
            write_timeout=10,
        )
    except Exception as exc:
        raise ProductRepositoryError("product database connection failed") from exc


def _quote_identifier(identifier: str) -> str:
    return f"`{identifier.replace('`', '``')}`"


@lru_cache(maxsize=1)
def get_product_columns() -> tuple[dict[str, str], ...]:
    try:
        with _connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(f"DESCRIBE {_quote_identifier(PRODUCT_TABLE)}")
                rows = cursor.fetchall()
    except Exception as exc:
        if isinstance(exc, ProductRepositoryError):
            raise
        raise ProductRepositoryError("product table metadata lookup failed") from exc

    return tuple({"name": row["Field"], "type": row["Type"].lower()} for row in rows)


def _is_text_column(column_type: str) -> bool:
    return any(type_name in column_type for type_name in TEXT_COLUMN_TYPES)


def _is_number_column(column_type: str) -> bool:
    return any(type_name in column_type for type_name in NUMBER_COLUMN_TYPES)


def _selectable_columns(columns: tuple[dict[str, str], ...]) -> list[str]:
    names = [column["name"] for column in columns]
    preferred = [name for name in PREFERRED_OUTPUT_COLUMNS if name in names]
    fallback = [name for name in names if name not in preferred]
    return [*preferred, *fallback][:12]


def _searchable_text_columns(columns: tuple[dict[str, str], ...]) -> list[str]:
    names = {column["name"] for column in columns}
    preferred = [name for name in PREFERRED_TEXT_COLUMNS if name in names]
    fallback = [
        column["name"]
        for column in columns
        if column["name"] not in preferred and _is_text_column(column["type"])
    ]
    return [*preferred, *fallback]


def _price_columns(columns: tuple[dict[str, str], ...]) -> list[str]:
    return [
        column["name"]
        for column in columns
        if _is_number_column(column["type"]) and "price" in column["name"].lower()
    ]


def _extract_terms(message: str) -> list[str]:
    raw_terms = re.findall(r"[0-9A-Za-z가-힣]+", message.lower())
    terms: list[str] = []
    for term in raw_terms:
        if len(term) < 2 or term in STOPWORDS or term in terms:
            continue
        terms.append(term)
        if len(terms) >= MAX_SEARCH_TERMS:
            break
    return terms


def _extract_price_limit(message: str) -> int | None:
    normalized = message.replace(",", "")
    match = re.search(r"(\d+)\s*만\s*원", normalized)
    if match:
        return int(match.group(1)) * 10000

    match = re.search(r"(\d{4,})\s*원", normalized)
    if match:
        return int(match.group(1))

    return None


def _compact_product(row: dict[str, Any]) -> dict[str, Any]:
    compacted: dict[str, Any] = {}
    for key, value in row.items():
        if value is None or value == "":
            continue
        if isinstance(value, str) and len(value) > 180:
            value = value[:177].rstrip() + "..."
        compacted[key] = value
    return compacted


def search_products(message: str, limit: int = MAX_RECOMMENDATIONS) -> list[dict[str, Any]]:
    columns = get_product_columns()
    select_columns = _selectable_columns(columns)
    text_columns = _searchable_text_columns(columns)
    price_columns = _price_columns(columns)
    terms = _extract_terms(message)
    price_limit = _extract_price_limit(message)

    where_clauses: list[str] = []
    params: list[Any] = []
    if terms and text_columns:
        term_clauses = []
        for term in terms:
            column_clauses = [f"{_quote_identifier(column)} LIKE %s" for column in text_columns]
            term_clauses.append("(" + " OR ".join(column_clauses) + ")")
            params.extend([f"%{term}%"] * len(text_columns))
        where_clauses.append("(" + " OR ".join(term_clauses) + ")")

    if price_limit is not None and price_columns:
        price_clause = " OR ".join(f"{_quote_identifier(column)} <= %s" for column in price_columns)
        where_clauses.append(f"({price_clause})")
        params.extend([price_limit] * len(price_columns))

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    order_sql = ""
    if price_columns:
        order_sql = f"ORDER BY {_quote_identifier(price_columns[0])} ASC"

    sql = (
        f"SELECT {', '.join(_quote_identifier(column) for column in select_columns)} "
        f"FROM {_quote_identifier(PRODUCT_TABLE)} "
        f"{where_sql} "
        f"{order_sql} "
        f"LIMIT %s"
    )
    params.append(limit)

    try:
        with _connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, params)
                rows = cursor.fetchall()
    except Exception as exc:
        if isinstance(exc, ProductRepositoryError):
            raise
        raise ProductRepositoryError("product lookup failed") from exc

    return [_compact_product(row) for row in rows]


def format_products_for_prompt(products: list[dict[str, Any]]) -> str:
    if not products:
        return "상품 DB에서 질문과 직접 연결되는 상품 후보를 찾지 못했습니다."

    lines = ["상품 DB에서 조회한 추천 후보:"]
    for index, product in enumerate(products, start=1):
        fields = ", ".join(f"{key}: {value}" for key, value in product.items())
        lines.append(f"{index}. {fields}")
    return "\n".join(lines)
