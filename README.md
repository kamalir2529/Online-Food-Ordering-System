# Online Food Ordering & Restaurant Sales Analysis System

A full-stack food ordering and restaurant analytics application built using **Python (Flask, Pandas, Matplotlib)**, **Java (JDBC)**, and **MySQL**.

## Features
- **Web Interface (`app.py`):** Add new customers, browse the restaurant menu, place live food orders, and monitor real-time revenue, order count, and top-selling dishes.
- **CLI Management System (`FoodOrderingSystem.java`):** Menu-driven Java JDBC console application for order placement, status updates, and sales reporting.
- **Sales Analytics & Visualization (`sales_analysis.py`):** Generates bar charts for popular menu items and line charts for daily revenue trends (`sales_analysis_charts.png`).
- **Relational Database (`database_setup.sql`):** Normalized MySQL schema (`restaurant_db`) managing `customers`, `menu`, `orders`, and `order_items`.

## How to Run
1. Import `database_setup.sql` into MySQL (`restaurant_db`).
2. Install Python dependencies:
   ```bash
   pip install flask mysql-connector-python pandas matplotlib