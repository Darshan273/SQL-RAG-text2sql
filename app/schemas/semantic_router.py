import json
from app.schemas.registry import SCHEMA_SLICES, merge_slices

async def semantic_route(user_query: str, groq_client) -> list[str]:
    system_prompt = """You are a database query router for an e-commerce database.
Given a user query, identify which database domains are needed to answer it.

Available domains:
- query_orders: revenue, sales, payments, shipping, order dates, 
                purchase history, money spent, transactions
- query_products: product names, categories, brands, prices, 
                  stock levels, inventory, item details
- query_customers: customer names, emails, gender, country, signup date,
                   highest spenders, biggest purchasers, valuable customers,
                   who buys most, user profiles
- query_reviews: ratings, feedback, review text, sentiment, 
                 satisfaction, star ratings, opinions

Rules:
- Return ONLY a valid JSON array of domain names
- Include multiple domains if a JOIN is needed
- Examples:
  'total revenue by country' -> ["query_orders"]
  'top spending customers' -> ["query_customers", "query_orders"]
  'products never reviewed' -> ["query_products", "query_reviews"]
  'highest spenders from India' -> ["query_customers", "query_orders"]
  'who buys most Electronics' -> ["query_customers", "query_orders", "query_products"]
- Return ONLY the JSON array. No explanation. No markdown."""

    try:
        response = await groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ],
            max_tokens=60,
            temperature=0,
        )
        content = response.choices[0].message.content.strip()
        parsed = json.loads(content)
        
        valid_tools = {"query_orders", "query_products", "query_customers", "query_reviews"}
        if isinstance(parsed, list) and len(parsed) > 0 and all(tool in valid_tools for tool in parsed):
            return parsed
        return ["query_cross_domain"]
    except Exception:
        return ["query_cross_domain"]

def get_schema_for_tools(tool_names: list[str]) -> str:
    if len(tool_names) == 1:
        if tool_names[0] in SCHEMA_SLICES:
            return SCHEMA_SLICES[tool_names[0]]
        return SCHEMA_SLICES["query_cross_domain"]
    
    if len(tool_names) >= 2:
        return merge_slices(tool_names)
        
    return SCHEMA_SLICES["query_cross_domain"]
