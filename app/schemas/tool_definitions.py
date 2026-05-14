TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "query_orders",
            "description": (
                "Use when the query involves orders, revenue, total sales, "
                "payment methods, shipping countries, purchased products, "
                "order items, item quantity, or unit price."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "user_query": {
                        "type": "string",
                        "description": "The user's natural-language analytics question.",
                    }
                },
                "required": ["user_query"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_products",
            "description": (
                "Use when the query is only about products, product names, "
                "categories, brands, prices, stock quantity, or inventory."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "user_query": {
                        "type": "string",
                        "description": "The user's natural-language analytics question.",
                    }
                },
                "required": ["user_query"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_customers",
            "description": (
                "Use when the query is only about customers, names, emails, "
                "gender, signup dates, registration timing, or customer countries."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "user_query": {
                        "type": "string",
                        "description": "The user's natural-language analytics question.",
                    }
                },
                "required": ["user_query"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_reviews",
            "description": (
                "Use when the query involves product reviews, ratings, review text, "
                "review dates, feedback, comments, or product names attached to reviews."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "user_query": {
                        "type": "string",
                        "description": "The user's natural-language analytics question.",
                    }
                },
                "required": ["user_query"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_cross_domain",
            "description": (
                "Use when the query spans two or more domains, such as customers "
                "with orders, products with sales, reviews by customer segment, "
                "or revenue grouped by product/category/brand/customer attributes."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "user_query": {
                        "type": "string",
                        "description": "The user's natural-language analytics question.",
                    },
                    "tool_names": {
                        "type": "array",
                        "description": (
                            "The domain tools needed to answer the question. "
                            "Use two or more values."
                        ),
                        "items": {
                            "type": "string",
                            "enum": [
                                "query_orders",
                                "query_products",
                                "query_customers",
                                "query_reviews",
                            ],
                        },
                        "minItems": 2,
                        "uniqueItems": True,
                    },
                },
                "required": ["user_query", "tool_names"],
                "additionalProperties": False,
            },
        },
    },
]
