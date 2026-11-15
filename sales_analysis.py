import mysql.connector
import pandas as pd
import matplotlib.pyplot as plt

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root123!",
    database="restaurant_db"
)

orders_query = """
SELECT o.order_id, o.order_date, o.total_amount, o.order_status,
       m.item_name, m.category, oi.quantity, oi.subtotal
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
JOIN menu m ON oi.item_id = m.item_id
"""
df = pd.read_sql(orders_query, conn)
conn.close()

df['order_date'] = pd.to_datetime(df['order_date'])
df['date_only'] = df['order_date'].dt.date
valid_orders = df[df['order_status'] != 'Cancelled'].copy()

print("--- Preprocessed Sales Data ---")
print(valid_orders.head())

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

popular_items = valid_orders.groupby('item_name')['quantity'].sum().sort_values(ascending=False)
popular_items.plot(kind='bar', ax=axes[0], color='teal', edgecolor='black')
axes[0].set_title('Popular Menu Items (Units Sold)')
axes[0].set_xlabel('Menu Item')
axes[0].set_ylabel('Total Quantity Sold')
axes[0].tick_params(axis='x', rotation=30)

daily_sales = valid_orders.groupby('date_only')['subtotal'].sum()
daily_sales.plot(kind='line', marker='o', ax=axes[1], color='darkorange', linewidth=2)
axes[1].set_title('Daily Sales Trend')
axes[1].set_xlabel('Date')
axes[1].set_ylabel('Total Sales (Rs.)')
axes[1].grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
plt.savefig('sales_analysis_charts.png', dpi=300)
plt.show()
print("Charts saved successfully as 'sales_analysis_charts.png'")