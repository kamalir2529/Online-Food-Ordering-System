from flask import Flask, render_template_string, request, redirect
import mysql.connector

app = Flask(__name__)

def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="root123!",
        database="restaurant_db"
    )

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Online Food Ordering & Sales Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; background: #f4f6f9; color: #333; }
        header { background: #ff5722; color: white; padding: 15px 30px; text-align: center; }
        .container { max-width: 1000px; margin: 20px auto; padding: 20px; background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        h2 { border-bottom: 2px solid #ff5722; padding-bottom: 5px; color: #ff5722; }
        table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
        th, td { padding: 10px; border: 1px solid #ddd; text-align: left; }
        th { background: #333; color: white; }
        .btn { background: #ff5722; color: white; padding: 10px 18px; border: none; border-radius: 5px; cursor: pointer; font-size: 15px; }
        .btn:hover { background: #e64a19; }
        .stats { display: flex; gap: 20px; margin-bottom: 20px; }
        .card { flex: 1; background: #fff3e0; padding: 15px; border-radius: 8px; text-align: center; border-left: 5px solid #ff5722; }
        .row { display: flex; gap: 10px; margin-bottom: 15px; }
        input, select { padding: 8px; margin: 5px 0; width: 100%; box-sizing: border-box; }
    </style>
</head>
<body>
<header>
    <h1>Online Food Ordering & Restaurant Sales System</h1>
    <p>Scenario 12 | Register No: 732925ITR042</p>
</header>

<div class="container">
    <div class="stats">
        <div class="card"><h3>Total Orders</h3><h1>{{ total_orders }}</h1></div>
        <div class="card"><h3>Total Revenue</h3><h1>Rs. {{ total_revenue }}</h1></div>
        <div class="card"><h3>Top Dish</h3><h1>{{ top_item }}</h1></div>
    </div>

    <h2>1. Add New Customer</h2>
    <form method="POST" action="/add_customer" class="row">
        <input type="text" name="customer_name" placeholder="Customer Name (e.g., Priya Sharma)" required>
        <input type="text" name="phone" placeholder="Phone Number (e.g., 9876501234)" required>
        <button type="submit" class="btn">Add Customer</button>
    </form>

    <h2>2. Restaurant Menu & Place Order</h2>
    <form method="POST" action="/order">
        <label>Select Customer:</label>
        <select name="customer_id" required>
            {% for c in customers %}
            <option value="{{ c.customer_id }}">{{ c.customer_name }} ({{ c.phone }})</option>
            {% endfor %}
        </select>

        <table>
            <tr><th>ID</th><th>Food Item</th><th>Category</th><th>Price (Rs.)</th><th>Quantity</th></tr>
            {% for item in menu %}
            <tr>
                <td>{{ item.item_id }}</td>
                <td>{{ item.item_name }}</td>
                <td>{{ item.category }}</td>
                <td>{{ item.price }}</td>
                <td><input type="number" name="qty_{{ item.item_id }}" value="0" min="0" max="20"></td>
            </tr>
            {% endfor %}
        </table>
        <button type="submit" class="btn">Place Food Order</button>
    </form>

    <h2>3. Recent Orders & Status</h2>
    <table>
        <tr><th>Order ID</th><th>Customer</th><th>Date</th><th>Total (Rs.)</th><th>Status</th></tr>
        {% for o in orders %}
        <tr>
            <td>#{{ o.order_id }}</td>
            <td>{{ o.customer_name }}</td>
            <td>{{ o.order_date }}</td>
            <td>{{ o.total_amount }}</td>
            <td><b>{{ o.order_status }}</b></td>
        </tr>
        {% endfor %}
    </table>
</div>
</body>
</html>
"""

@app.route("/")
def index():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM menu WHERE is_available = TRUE")
    menu = cursor.fetchall()

    cursor.execute("SELECT * FROM customers ORDER BY customer_id DESC")
    customers = cursor.fetchall()

    cursor.execute("""
        SELECT o.order_id, c.customer_name, o.order_date, o.total_amount, o.order_status
        FROM orders o JOIN customers c ON o.customer_id = c.customer_id
        ORDER BY o.order_id DESC
    """)
    orders = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) AS cnt, COALESCE(SUM(total_amount),0) AS rev FROM orders WHERE order_status != 'Cancelled'")
    summary = cursor.fetchone()

    cursor.execute("""
        SELECT m.item_name, SUM(oi.quantity) AS sold
        FROM order_items oi JOIN menu m ON oi.item_id = m.item_id
        GROUP BY m.item_name ORDER BY sold DESC LIMIT 1
    """)
    top = cursor.fetchone()
    top_item = top["item_name"] if top else "N/A"

    conn.close()
    return render_template_string(
        HTML_PAGE,
        menu=menu,
        customers=customers,
        orders=orders,
        total_orders=summary["cnt"],
        total_revenue=summary["rev"],
        top_item=top_item
    )

@app.route("/add_customer", methods=["POST"])
def add_customer():
    name = request.form.get("customer_name")
    phone = request.form.get("phone")
    email = request.form.get("email")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO customers (customer_name, phone, email) VALUES (%s, %s, %s)",
        (name, phone, email)
    )
    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/order", methods=["POST"])
def place_order():
    cust_id = request.form.get("customer_id")
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM menu WHERE is_available = TRUE")
    menu = cursor.fetchall()

    cursor.execute("INSERT INTO orders (customer_id, total_amount, order_status) VALUES (%s, 0, 'Placed')", (cust_id,))
    order_id = cursor.lastrowid
    grand_total = 0

    for item in menu:
        qty = int(request.form.get(f"qty_{item['item_id']}", 0))
        if qty > 0:
            subtotal = float(item["price"]) * qty
            grand_total += subtotal
            cursor.execute(
                "INSERT INTO order_items (order_id, item_id, quantity, subtotal) VALUES (%s, %s, %s, %s)",
                (order_id, item["item_id"], qty, subtotal)
            )

    cursor.execute("UPDATE orders SET total_amount = %s WHERE order_id = %s", (grand_total, order_id))
    conn.commit()
    conn.close()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)