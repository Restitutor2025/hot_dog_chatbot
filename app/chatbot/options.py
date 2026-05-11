#
#  options.py
#  hot_dog_chatbot
#
#  Created by Codex on 2026-04-29.
#  Updated by Codex on 2026-05-11.
#  Updated by God_Zero on 2026-05-07.
#
#  Codex Update Log:
#  - 2026-04-29: Centralized button options, rule-based replies, and the system prompt.
#  - 2026-05-07: Preserved existing hardcoded option data and customer-service limits.
#  - 2026-05-11: Merged product DB lookup helpers into this chatbot options module.
#
#  God_Zero Update Log:
#  - 2026-05-07: God_Zero님 added session-memory behavior guidance to the system prompt.
#

from __future__ import annotations

from dataclasses import dataclass
import re
from functools import lru_cache
from typing import Any

import pymysql
from pymysql.cursors import DictCursor

import config

# Get DB Data Required

USER_ID = "더미사용자"
MAIN_STEP = "main"
PRODUCT_STEP = "product"
INQUIRY_STEP = "inquiry"

GREETINGS = "안녕하세요!" + USER_ID + "님! 무엇을 도와 드릴까요?"
ERROR_INFO = "현재 챗봇의 이용이 어렵습니다. 관리자에게 직접 문의바랍니다."
ERROR_NETWORK = "연결이 불안정합니다. 네트워크를 확인 해주세요."
ERROR_NO_DATA = "죄송합니다. 구매 이력정보가 존재하지 않습니다. 실제로 구매했던 상품이 맞는지 확인 해주세요."

ERROR_DB_CONNECTION_MANAGER = "사용자: " + USER_ID + "DB와 연결이 되지 않았습니다."
ERROR_DB_DATA_MANAGER = (
    "사용자: " + USER_ID + "DB의 데이터를 가져오는 중에 오류가 발생했습니다."
)

MAIN_OPTIONS = ["제품", "문의"]

PRODUCT_OPTIONS = [
    "카테고리",
    "가격대",
    "나이대",
    "브랜드",
    "사이즈 문의",
    "견종/몸무게 적합성 문의",
    "알러지/성분 문의",
    "재질/관리 방법 문의",
    "상품 비교 문의",
    "재고/재입고 문의",
]

INQUIRY_OPTIONS = [
    "주문/결제 문의",
    "배송 문의",
    "교환/반품/환불 문의",
    "상품 정보 문의",
    "쿠폰/포인트 문의",
    "회원/계정 문의",
    "기타 문의",
]

CATEGORY_OPTIONS = {
    PRODUCT_STEP: PRODUCT_OPTIONS,
    INQUIRY_STEP: INQUIRY_OPTIONS,
}

MAIN_SELECTIONS = {
    "제품": {
        "answer": "제품 관련 문의 유형을 선택해 주세요.",
        "next_step": PRODUCT_STEP,
        "options": PRODUCT_OPTIONS,
    },
    "문의": {
        "answer": "문의하실 항목을 선택해 주세요.",
        "next_step": INQUIRY_STEP,
        "options": INQUIRY_OPTIONS,
    },
}

OPTION_RESPONSES = {
    "카테고리": "애견용 옷, 하네스, 사료, 장난감, 입마개 카테고리로 안내할 수 있습니다. 상세 상품 목록은 앱의 상품 DB 연동 후 확인 가능합니다.",
    "가격대": "원하시는 예산대를 알려주시면 적합한 상품 유형을 안내해 드릴 수 있습니다. 실제 가격은 앱의 상품 DB 연동 후 확인 가능합니다.",
    "나이대": "강아지의 나이와 생활 패턴에 따라 사료, 장난감, 하네스 선택 기준을 안내해 드릴 수 있습니다.",
    "브랜드": "현재 브랜드별 실제 상품 정보는 확정할 수 없습니다. 앱의 상품 DB 연동 후 브랜드 목록과 상품을 확인할 수 있습니다.",
    "사이즈 문의": "목둘레, 가슴둘레, 등길이, 몸무게를 알려주시면 옷이나 하네스 사이즈 선택 기준을 안내해 드릴게요.",
    "견종/몸무게 적합성 문의": "견종, 몸무게, 체형을 알려주시면 옷, 하네스, 입마개 선택 시 확인할 기준을 안내해 드릴 수 있습니다.",
    "알러지/성분 문의": "알러지 이력이 있다면 원료와 성분표 확인이 중요합니다. 실제 성분 정보는 앱의 상품 DB 연동 후 확인 가능합니다.",
    "재질/관리 방법 문의": "제품 재질에 따라 세탁, 건조, 보관 방법이 달라질 수 있습니다. 실제 관리법은 상품 상세 정보 연동 후 더 정확히 안내할 수 있습니다.",
    "상품 비교 문의": "비교하고 싶은 상품 유형이나 조건을 알려주시면 장단점 기준을 정리해 드릴게요. 실제 상품 비교는 앱의 상품 DB 연동 후 가능합니다.",
    "재고/재입고 문의": "실제 재고와 재입고 일정은 확정할 수 없습니다. 앱의 상품 DB 연동 후 확인 가능합니다.",
    "주문/결제 문의": "주문 상태, 결제 승인, 결제 수단 변경은 앱의 주문 DB 연동 후 확인 가능합니다.",
    "배송 문의": "배송 상태, 송장 번호, 도착 예정일은 앱의 주문/배송 DB 연동 후 확인 가능합니다.",
    "교환/반품/환불 문의": "교환, 반품, 환불 가능 여부는 주문 정보와 상품 정책 확인이 필요합니다. 앱의 주문 DB 연동 후 안내 가능합니다.",
    "상품 정보 문의": "상품 상세 정보, 옵션, 실제 판매 상태는 앱의 상품 DB 연동 후 확인 가능합니다.",
    "쿠폰/포인트 문의": "쿠폰 적용 가능 여부와 포인트 잔액은 앱의 회원/혜택 DB 연동 후 확인 가능합니다.",
    "회원/계정 문의": "로그인, 회원 정보, 계정 상태는 앱의 회원 DB 연동 후 확인 가능합니다.",
    "기타 문의": "궁금한 내용을 직접 입력해 주세요. 애견 쇼핑 관련 범위에서 가능한 안내를 드리겠습니다.",
}

ALL_SELECTABLE_OPTIONS = [
    *MAIN_OPTIONS,
    *PRODUCT_OPTIONS,
    *INQUIRY_OPTIONS,
]

PRODUCT_TABLE = "product"
BUY_TABLE = "buy"
DELIVER_TABLE = "deliver"
MAX_RECOMMENDATIONS = 5
MAX_HISTORY_ROWS = 5
MAX_SEARCH_TERMS = 8
TEXT_COLUMN_TYPES = ("char", "text", "enum", "set", "json")
NUMBER_COLUMN_TYPES = ("int", "decimal", "float", "double", "real")
BINARY_COLUMN_TYPES = ("blob", "binary", "varbinary")
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
TERM_SUFFIXES = (
    "해주세요",
    "해줘",
    "주세요",
    "알려주세요",
    "알려줘",
    "있나요",
    "있어",
    "추천",
    "문의",
)

BUY_INTENT_KEYWORDS = (
    "구매",
    "구입",
    "주문",
    "결제",
    "환불",
    "반품",
    "교환",
    "취소",
    "내역",
    "샀",
    "산",
    "buy",
    "order",
    "payment",
    "refund",
)
DELIVER_INTENT_KEYWORDS = (
    "배송",
    "배달",
    "택배",
    "송장",
    "운송장",
    "도착",
    "출고",
    "delivery",
    "deliver",
)

SYSTEM_PROMPT = """당신은 애견 쇼핑 앱의 고객 응대 챗봇입니다.
앱은 애견용 옷, 하네스, 사료, 장난감, 입마개를 판매합니다.
사용자가 직접 질문하면 친절하고 짧게 한국어로 답변하세요.
반드시 config.py파일을 읽어 DB에 연동한 후 응답하세요. DB에 없는 데이터를 절대로 추론하지 마세요.
같은 session_id로 이어지는 대화에서는 이전 대화 내용을 참고해 세션별로 기억을 한 상태로 연속된 대화를 하세요.
사이즈, 견종, 몸무게, 나이, 알러지, 재질, 관리법처럼 구매 판단에 필요한 기준을 안내하세요.
실제 상품 재고, 실제 가격, 실제 주문/결제/배송/환불 상태는 확정하지 마세요.
상품 DB에서 조회한 추천 후보가 제공되면 그 후보 안에서만 상품명, 가격, 카테고리, 브랜드 등 확인 가능한 정보를 활용해 추천하세요.
주문/결제/배송/환불에 대한 정보는 반드시 DB의 buy, deliver 테이블에 해당 사용자와 해당 애완견에 대한 정보를 참조하며 존재하지 않을 경우에는
ERROR_NO_DATA로 응답하세요.
주문/결제/배송/환불 정보는 "앱의 상품/주문 내역이 있는 경우에만 확인 가능"하다고 안내하세요.
데이터셋, CSV, 벡터 인덱스, 외부 API를 사용한다고 말하지 마세요."""


class ProductRepositoryError(RuntimeError):
    def __init__(self, message: str, user_message: str = ERROR_INFO):
        super().__init__(message)
        self.user_message = user_message


@dataclass(frozen=True)
class ChatDatabaseContext:
    source: str
    prompt: str
    records: list[dict[str, Any]]


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
        raise ProductRepositoryError(
            "product database connection failed",
            ERROR_NETWORK,
        ) from exc


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


def _is_binary_column(column_type: str) -> bool:
    return any(type_name in column_type for type_name in BINARY_COLUMN_TYPES)


def _selectable_columns(columns: tuple[dict[str, str], ...]) -> list[str]:
    names = [column["name"] for column in columns]
    preferred = [name for name in PREFERRED_OUTPUT_COLUMNS if name in names]
    fallback = [
        column["name"]
        for column in columns
        if column["name"] not in preferred and not _is_binary_column(column["type"])
    ]
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
        for suffix in TERM_SUFFIXES:
            if term.endswith(suffix) and len(term) > len(suffix):
                term = term[: -len(suffix)]
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


def _compact_row(row: dict[str, Any]) -> dict[str, Any]:
    compacted: dict[str, Any] = {}
    for key, value in row.items():
        if value is None or value == "":
            continue
        if isinstance(value, bytes | bytearray | memoryview):
            continue
        if hasattr(value, "isoformat"):
            value = value.isoformat(sep=" ")
        if isinstance(value, str) and len(value) > 180:
            value = value[:177].rstrip() + "..."
        compacted[key] = value
    return compacted


def _compact_product(row: dict[str, Any]) -> dict[str, Any]:
    return _compact_row(row)


def _contains_any_keyword(message: str, keywords: tuple[str, ...]) -> bool:
    lowered = message.lower()
    return any(keyword in lowered for keyword in keywords)


def resolve_lookup_source(message: str) -> str:
    if _contains_any_keyword(message, DELIVER_INTENT_KEYWORDS):
        return DELIVER_TABLE
    if _contains_any_keyword(message, BUY_INTENT_KEYWORDS):
        return BUY_TABLE
    return PRODUCT_TABLE


def _normalize_user_identifier(user_id: str | None) -> str | None:
    if user_id is not None and user_id.strip():
        return user_id.strip()
    if USER_ID.strip() and USER_ID != "더미사용자":
        return USER_ID.strip()
    return None


def _resolve_user_seq(
    connection: pymysql.connections.Connection,
    user_seq: int | None = None,
    user_id: str | None = None,
) -> int | None:
    if user_seq is not None:
        return user_seq

    user_identifier = _normalize_user_identifier(user_id)
    if user_identifier is None:
        return None

    if user_identifier.isdecimal():
        return int(user_identifier)

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT user_seq
            FROM users
            WHERE user_id = %s OR user_name = %s
            LIMIT 1
            """,
            (user_identifier, user_identifier),
        )
        row = cursor.fetchone()

    if not row:
        return None
    return row["user_seq"]


def search_products(
    message: str,
    limit: int = MAX_RECOMMENDATIONS,
    product_seq: int | None = None,
) -> list[dict[str, Any]]:
    terms = _extract_terms(message)
    price_limit = _extract_price_limit(message)

    where_clauses: list[str] = []
    params: list[Any] = []
    searchable_columns = (
        "p.product_name",
        "m.maker_name",
        "pc.product_category_name",
        "psc.product_sub_category_name",
        "db.dog_breeds_name",
        "ds.dog_size_name",
        "da.dog_age",
        "alg.dog_allergy_name",
    )
    if terms:
        term_clauses = []
        for term in terms:
            column_clauses = [f"{column} LIKE %s" for column in searchable_columns]
            term_clauses.append("(" + " OR ".join(column_clauses) + ")")
            params.extend([f"%{term}%"] * len(searchable_columns))
        where_clauses.append("(" + " OR ".join(term_clauses) + ")")

    if price_limit is not None:
        where_clauses.append("(p.product_price <= %s)")
        params.append(price_limit)

    if product_seq is not None:
        where_clauses.append("(p.product_seq = %s)")
        params.append(product_seq)

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    sql = f"""
        SELECT
            p.product_seq,
            p.product_name,
            p.product_qty,
            p.product_price,
            m.maker_name,
            pc.product_category_name,
            psc.product_sub_category_name,
            db.dog_breeds_name,
            ds.dog_size_name,
            da.dog_age,
            alg.dog_allergy_name
        FROM product p
        LEFT JOIN maker m ON m.maker_seq = p.maker_seq
        LEFT JOIN product_category pc ON pc.product_category_seq = p.product_category_seq
        LEFT JOIN product_sub_category psc ON psc.product_sub_category_seq = p.product_sub_category_seq
        LEFT JOIN dog_breeds db ON db.dog_breeds_seq = p.dog_breeds_seq
        LEFT JOIN dog_size ds ON ds.dog_size_seq = p.dog_size_seq
        LEFT JOIN dog_age da ON da.dog_age_seq = p.dog_age_seq
        LEFT JOIN dog_allergy alg ON alg.dog_allergy_seq = p.dog_allergy_seq
        {where_sql}
        ORDER BY p.product_price ASC, p.product_seq ASC
        LIMIT %s
    """
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


def search_buy_history(
    user_seq: int | None = None,
    user_id: str | None = None,
    buy_seq: int | None = None,
    product_seq: int | None = None,
    limit: int = MAX_HISTORY_ROWS,
) -> list[dict[str, Any]]:
    sql = """
        SELECT
            b.buy_seq,
            b.buy_date,
            b.buy_qty,
            b.buy_price,
            b.user_seq,
            b.product_seq,
            p.product_name,
            p.product_price
        FROM buy b
        LEFT JOIN product p ON p.product_seq = b.product_seq
        WHERE b.user_seq = %s
    """
    params: list[Any] = []

    try:
        with _connect() as connection:
            resolved_user_seq = _resolve_user_seq(connection, user_seq, user_id)
            if resolved_user_seq is None:
                return []

            params.append(resolved_user_seq)
            if buy_seq is not None:
                sql += " AND b.buy_seq = %s"
                params.append(buy_seq)
            if product_seq is not None:
                sql += " AND b.product_seq = %s"
                params.append(product_seq)

            sql += " ORDER BY b.buy_date DESC, b.buy_seq DESC LIMIT %s"
            params.append(limit)

            with connection.cursor() as cursor:
                cursor.execute(sql, params)
                rows = cursor.fetchall()
    except Exception as exc:
        if isinstance(exc, ProductRepositoryError):
            raise
        raise ProductRepositoryError("buy history lookup failed", ERROR_INFO) from exc

    return [_compact_row(row) for row in rows]


def search_deliver_history(
    user_seq: int | None = None,
    user_id: str | None = None,
    deliver_seq: int | None = None,
    buy_seq: int | None = None,
    product_seq: int | None = None,
    limit: int = MAX_HISTORY_ROWS,
) -> list[dict[str, Any]]:
    sql = """
        SELECT
            d.deliver_seq,
            d.user_seq,
            d.buy_seq,
            d.staff_seq,
            d.deliver_start_date,
            d.deliver_end_date,
            b.buy_date,
            b.buy_qty,
            b.buy_price,
            b.product_seq,
            p.product_name,
            p.product_price
        FROM deliver d
        LEFT JOIN buy b ON b.buy_seq = d.buy_seq
        LEFT JOIN product p ON p.product_seq = b.product_seq
        WHERE d.user_seq = %s
    """
    params: list[Any] = []

    try:
        with _connect() as connection:
            resolved_user_seq = _resolve_user_seq(connection, user_seq, user_id)
            if resolved_user_seq is None:
                return []

            params.append(resolved_user_seq)
            if deliver_seq is not None:
                sql += " AND d.deliver_seq = %s"
                params.append(deliver_seq)
            if buy_seq is not None:
                sql += " AND d.buy_seq = %s"
                params.append(buy_seq)
            if product_seq is not None:
                sql += " AND b.product_seq = %s"
                params.append(product_seq)

            sql += """
                ORDER BY
                    COALESCE(d.deliver_start_date, d.deliver_end_date) DESC,
                    d.deliver_seq DESC
                LIMIT %s
            """
            params.append(limit)

            with connection.cursor() as cursor:
                cursor.execute(sql, params)
                rows = cursor.fetchall()
    except Exception as exc:
        if isinstance(exc, ProductRepositoryError):
            raise
        raise ProductRepositoryError("deliver history lookup failed", ERROR_INFO) from exc

    return [_compact_row(row) for row in rows]


def format_products_for_prompt(products: list[dict[str, Any]]) -> str:
    if not products:
        return ERROR_NO_DATA

    lines = ["상품 DB에서 조회한 추천 후보:"]
    for index, product in enumerate(products, start=1):
        fields = ", ".join(f"{key}: {value}" for key, value in product.items())
        lines.append(f"{index}. {fields}")
    return "\n".join(lines)


def format_records_for_prompt(source: str, records: list[dict[str, Any]]) -> str:
    if not records:
        return ERROR_NO_DATA

    title_by_source = {
        BUY_TABLE: "구매 DB에서 조회한 구매 내역:",
        DELIVER_TABLE: "배송 DB에서 조회한 배송 내역:",
    }
    lines = [title_by_source.get(source, "DB에서 조회한 내역:")]
    for index, record in enumerate(records, start=1):
        fields = ", ".join(f"{key}: {value}" for key, value in record.items())
        lines.append(f"{index}. {fields}")
    return "\n".join(lines)


def build_database_context_for_message(
    message: str,
    user_seq: int | None = None,
    user_id: str | None = None,
    buy_seq: int | None = None,
    deliver_seq: int | None = None,
    product_seq: int | None = None,
) -> ChatDatabaseContext:
    source = resolve_lookup_source(message)
    if source == DELIVER_TABLE:
        records = search_deliver_history(
            user_seq=user_seq,
            user_id=user_id,
            deliver_seq=deliver_seq,
            buy_seq=buy_seq,
            product_seq=product_seq,
        )
        return ChatDatabaseContext(source, format_records_for_prompt(source, records), records)

    if source == BUY_TABLE:
        records = search_buy_history(
            user_seq=user_seq,
            user_id=user_id,
            buy_seq=buy_seq,
            product_seq=product_seq,
        )
        return ChatDatabaseContext(source, format_records_for_prompt(source, records), records)

    records = search_products(message, product_seq=product_seq)
    return ChatDatabaseContext(source, format_products_for_prompt(records), records)
