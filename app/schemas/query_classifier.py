def classify_query_type(user_query: str) -> str:
    query_lower = user_query.lower()
    
    if any(kw in query_lower for kw in ["never", "no ", "without"]):
        return "left_join_never"
        
    if any(kw in query_lower for kw in ["top", "most", "highest", "lowest", "rank"]):
        return "aggregation"
        
    tools_matched = 0
    if any(w in query_lower for w in ["customer", "user", "who", "people"]): tools_matched += 1
    if any(w in query_lower for w in ["product", "item", "brand", "category"]): tools_matched += 1
    if any(w in query_lower for w in ["order", "revenue", "sales", "bought"]): tools_matched += 1
    if any(w in query_lower for w in ["review", "rating", "feedback"]): tools_matched += 1
    
    if tools_matched >= 3:
        return "three_table_join"
    if tools_matched == 2:
        return "join_two_tables"
        
    return "simple_select"
