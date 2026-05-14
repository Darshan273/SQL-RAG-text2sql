ORDERED_DOMAIN_TOOLS = [
    "query_orders",
    "query_products",
    "query_customers",
    "query_reviews",
]

ORDERS_SCHEMA = """orders(order_id,customer_id,order_date,total_amount,payment_method,shipping_country)
order_items(order_item_id,order_id,product_id,quantity,unit_price)
FK: order_items.order_id=orders.order_id
Nullable: none
Joins: customer_id, order_id, product_id
Categorical: payment_method: ('credit_card', 'debit_card', 'paypal', 'cash')"""

PRODUCTS_SCHEMA = """products(product_id,product_name,category,price,stock_quantity,brand)
Nullable: brand
Joins: product_id
Categorical: category: ('Electronics', 'Clothing', 'Books', 'Food')"""

CUSTOMERS_SCHEMA = """customers(customer_id,name,email,gender,signup_date,country)
Nullable: gender, country
Joins: customer_id
Categorical: gender: ('Male', 'Female', 'Other')"""

REVIEWS_SCHEMA = """product_reviews(review_id,product_id,customer_id,rating,review_text,review_date)
products(product_id,product_name)
FK: product_reviews.product_id=products.product_id
Nullable: review_text
Joins: product_id, customer_id
Categorical: rating: (1, 2, 3, 4, 5)"""

DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "query_orders": [
        "order",
        "revenue",
        "payment",
        "shipping",
        "purchase",
        "bought",
        "spent",
        "sales",
        "total amount",
        "placed",
    ],
    "query_products": [
        "product",
        "category",
        "brand",
        "stock",
        "price",
        "item",
    ],
    "query_customers": [
        "customer",
        "user",
        "signup",
        "gender",
        "country",
        "email",
        "who",
        "never",
        "people",
        "person",
    ],
    "query_reviews": [
        "review",
        "rating",
        "feedback",
        "rated",
        "sentiment",
    ],
}

BASE_SCHEMA_SLICES: dict[str, str] = {
    "query_orders": ORDERS_SCHEMA,
    "query_products": PRODUCTS_SCHEMA,
    "query_customers": CUSTOMERS_SCHEMA,
    "query_reviews": REVIEWS_SCHEMA,
}

COMPACT_CROSS_DOMAIN_LINES: dict[str, list[str]] = {
    "query_orders": [
        "orders(order_id,customer_id)",
        "order_items(order_id,product_id)",
    ],
    "query_products": ["products(product_id)"],
    "query_customers": ["customers(customer_id)"],
    "query_reviews": [
        "product_reviews(product_id,customer_id)",
    ],
}


def merge_slices(tool_names: list[str]) -> str:
    selected = set(tool_names)
    selected_tools = [
        tool_name
        for tool_name in ORDERED_DOMAIN_TOOLS
        if tool_name in selected
    ]

    merged_lines: list[str] = []
    seen_lines: set[str] = set()

    for tool_name in selected_tools:
        for line in BASE_SCHEMA_SLICES[tool_name].splitlines():
            clean_line = line.strip()
            if clean_line and clean_line not in seen_lines:
                merged_lines.append(clean_line)
                seen_lines.add(clean_line)

    fk_lines: list[str] = []

    if {"query_customers", "query_orders"}.issubset(selected):
        fk_lines.append("FK: orders.customer_id=customers.customer_id")

    if {"query_orders", "query_products"}.issubset(selected):
        fk_lines.append("FK: order_items.product_id=products.product_id")

    if {"query_customers", "query_reviews"}.issubset(selected):
        fk_lines.append("FK: product_reviews.customer_id=customers.customer_id")

    for fk_line in fk_lines:
        if fk_line not in seen_lines:
            merged_lines.append(fk_line)
            seen_lines.add(fk_line)

    merged = "\n".join(merged_lines)
    if len(merged) <= 300:
        return merged

    compact_lines: list[str] = []
    seen_compact_lines: set[str] = set()

    for tool_name in selected_tools:
        for line in COMPACT_CROSS_DOMAIN_LINES[tool_name]:
            if line not in seen_compact_lines:
                compact_lines.append(line)
                seen_compact_lines.add(line)

    if "query_orders" in selected and len(selected_tools) < len(ORDERED_DOMAIN_TOOLS):
        order_fk = "FK: order_items.order_id=orders.order_id"
        if order_fk not in seen_compact_lines:
            compact_lines.append(order_fk)
            seen_compact_lines.add(order_fk)

    for fk_line in fk_lines:
        if fk_line not in seen_compact_lines:
            compact_lines.append(fk_line)
            seen_compact_lines.add(fk_line)

    return "\n".join(compact_lines)


SCHEMA_SLICES: dict[str, str] = {
    **BASE_SCHEMA_SLICES,
    "query_cross_domain": merge_slices(ORDERED_DOMAIN_TOOLS),
}


def detect_required_tools(user_query: str) -> list[str]:
    normalized_query = user_query.lower()
    matched_tools = [
        tool_name
        for tool_name in ORDERED_DOMAIN_TOOLS
        if any(keyword in normalized_query for keyword in DOMAIN_KEYWORDS[tool_name])
    ]

    if not matched_tools:
        return ["query_cross_domain"]

    return matched_tools
