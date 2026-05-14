FEW_SHOTS = {
    "simple_select": [
        {
            "question": "Show all products in Electronics category",
            "sql": "SELECT p.product_id, p.product_name, p.price FROM products p WHERE p.category = 'Electronics';"
        },
        {
            "question": "List customers from India",
            "sql": "SELECT c.customer_id, c.name, c.email FROM customers c WHERE c.country = 'India';"
        }
    ],
    "aggregation": [
        {
            "question": "Total revenue by payment method",
            "sql": "SELECT o.payment_method, SUM(o.total_amount) AS total_revenue FROM orders o GROUP BY o.payment_method;"
        },
        {
            "question": "Average product price per category",
            "sql": "SELECT p.category, AVG(p.price) AS avg_price FROM products p GROUP BY p.category;"
        }
    ],
    "join_two_tables": [
        {
            "question": "Show customer names with their total orders count",
            "sql": "SELECT c.name, COUNT(o.order_id) AS total_orders FROM customers c JOIN orders o ON c.customer_id = o.customer_id GROUP BY c.name;"
        },
        {
            "question": "List products that have been ordered at least once",
            "sql": "SELECT DISTINCT p.product_name FROM products p JOIN order_items oi ON p.product_id = oi.product_id;"
        }
    ],
    "left_join_never": [
        {
            "question": "Find customers who have never placed any order",
            "sql": "SELECT c.customer_id, c.name FROM customers c LEFT JOIN orders o ON c.customer_id = o.customer_id WHERE o.order_id IS NULL;"
        },
        {
            "question": "Show products that have never been reviewed",
            "sql": "SELECT p.product_id, p.product_name FROM products p LEFT JOIN product_reviews pr ON p.product_id = pr.product_id WHERE pr.review_id IS NULL;"
        }
    ],
    "three_table_join": [
        {
            "question": "Top 5 customers by total amount spent",
            "sql": "SELECT c.name, SUM(o.total_amount) AS amount_spent FROM customers c JOIN orders o ON c.customer_id = o.customer_id GROUP BY c.name ORDER BY amount_spent DESC LIMIT 5;"
        },
        {
            "question": "Which products were ordered most by quantity",
            "sql": "SELECT p.product_name, SUM(oi.quantity) AS total_quantity FROM products p JOIN order_items oi ON p.product_id = oi.product_id GROUP BY p.product_name ORDER BY total_quantity DESC LIMIT 1;"
        }
    ],
    "four_table_join": [
        {
            "question": "Customers who bought Electronics and also left a review",
            "sql": "SELECT DISTINCT c.name FROM customers c JOIN orders o ON c.customer_id = o.customer_id JOIN order_items oi ON o.order_id = oi.order_id JOIN products p ON oi.product_id = p.product_id JOIN product_reviews pr ON p.product_id = pr.product_id AND c.customer_id = pr.customer_id WHERE p.category = 'Electronics';"
        },
        {
            "question": "Show brand name with average rating and total sales",
            "sql": "SELECT p.brand, AVG(pr.rating) AS avg_rating, SUM(oi.quantity * oi.unit_price) AS total_sales FROM products p JOIN order_items oi ON p.product_id = oi.product_id JOIN orders o ON oi.order_id = o.order_id JOIN product_reviews pr ON p.product_id = pr.product_id GROUP BY p.brand;"
        }
    ]
}
