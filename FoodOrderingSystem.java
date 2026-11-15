import java.sql.*;
import java.util.Scanner;

public class FoodOrderingSystem {
    private static final String URL = "jdbc:mysql://localhost:3306/restaurant_db?useSSL=false&allowPublicKeyRetrieval=true";
    private static final String USER = "root";
    private static final String PASSWORD = "root123!";

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        try (Connection conn = DriverManager.getConnection(URL, USER, PASSWORD)) {
            while (true) {
                System.out.println("\n=== ONLINE FOOD ORDERING SYSTEM ===");
                System.out.println("1. View Menu");
                System.out.println("2. Add Menu Item");
                System.out.println("3. Register Customer");
                System.out.println("4. Place New Order");
                System.out.println("5. Update Order Status");
                System.out.println("6. View Sales & Popular Items Report");
                System.out.println("7. Exit");
                System.out.print("Enter choice: ");
                int choice = sc.nextInt();
                sc.nextLine();

                switch (choice) {
                    case 1 -> viewMenu(conn);
                    case 2 -> addMenuItem(conn, sc);
                    case 3 -> registerCustomer(conn, sc);
                    case 4 -> placeOrder(conn, sc);
                    case 5 -> updateOrderStatus(conn, sc);
                    case 6 -> generateReports(conn);
                    case 7 -> {
                        System.out.println("Exiting system...");
                        return;
                    }
                    default -> System.out.println("Invalid choice!");
                }
            }
        } catch (SQLException e) {
            System.out.println("ERROR MESSAGE: " + e.getMessage());
        }
    }

    private static void viewMenu(Connection conn) throws SQLException {
        String sql = "SELECT * FROM menu";
        try (Statement stmt = conn.createStatement(); ResultSet rs = stmt.executeQuery(sql)) {
            System.out.printf("\n%-5s %-25s %-15s %-10s %-10s\n", "ID", "Item Name", "Category", "Price", "Available");
            while (rs.next()) {
                System.out.printf("%-5d %-25s %-15s %-10.2f %-10s\n",
                        rs.getInt("item_id"), rs.getString("item_name"),
                        rs.getString("category"), rs.getDouble("price"),
                        rs.getBoolean("is_available") ? "Yes" : "No");
            }
        }
    }

    private static void addMenuItem(Connection conn, Scanner sc) throws SQLException {
        System.out.print("Item Name: ");
        String name = sc.nextLine();
        System.out.print("Category: ");
        String category = sc.nextLine();
        System.out.print("Price: ");
        double price = sc.nextDouble();

        String sql = "INSERT INTO menu (item_name, category, price, is_available) VALUES (?, ?, ?, TRUE)";
        try (PreparedStatement pstmt = conn.prepareStatement(sql)) {
            pstmt.setString(1, name);
            pstmt.setString(2, category);
            pstmt.setDouble(3, price);
            pstmt.executeUpdate();
            System.out.println("Menu item added successfully!");
        }
    }

    private static void registerCustomer(Connection conn, Scanner sc) throws SQLException {
        System.out.print("Customer Name: ");
        String name = sc.nextLine();
        System.out.print("Phone: ");
        String phone = sc.nextLine();
        System.out.print("Email: ");
        String email = sc.nextLine();

        String sql = "INSERT INTO customers (customer_name, phone, email) VALUES (?, ?, ?)";
        try (PreparedStatement pstmt = conn.prepareStatement(sql, Statement.RETURN_GENERATED_KEYS)) {
            pstmt.setString(1, name);
            pstmt.setString(2, phone);
            pstmt.setString(3, email);
            pstmt.executeUpdate();
            ResultSet keys = pstmt.getGeneratedKeys();
            if (keys.next()) {
                System.out.println("Customer registered with ID: " + keys.getInt(1));
            }
        }
    }

    private static void placeOrder(Connection conn, Scanner sc) throws SQLException {
        System.out.print("Enter Customer ID: ");
        int custId = sc.nextInt();

        String orderSql = "INSERT INTO orders (customer_id, total_amount, order_status) VALUES (?, 0, 'Placed')";
        int orderId;
        try (PreparedStatement pstmt = conn.prepareStatement(orderSql, Statement.RETURN_GENERATED_KEYS)) {
            pstmt.setInt(1, custId);
            pstmt.executeUpdate();
            ResultSet keys = pstmt.getGeneratedKeys();
            keys.next();
            orderId = keys.getInt(1);
        }

        double grandTotal = 0;
        while (true) {
            viewMenu(conn);
            System.out.print("Enter Menu Item ID to add (0 to finish): ");
            int itemId = sc.nextInt();
            if (itemId == 0) break;

            System.out.print("Enter Quantity: ");
            int qty = sc.nextInt();

            String priceSql = "SELECT price FROM menu WHERE item_id = ? AND is_available = TRUE";
            try (PreparedStatement pstmt = conn.prepareStatement(priceSql)) {
                pstmt.setInt(1, itemId);
                ResultSet rs = pstmt.executeQuery();
                if (rs.next()) {
                    double price = rs.getDouble("price");
                    double subtotal = price * qty;
                    grandTotal += subtotal;

                    String itemInsert = "INSERT INTO order_items (order_id, item_id, quantity, subtotal) VALUES (?, ?, ?, ?)";
                    try (PreparedStatement ins = conn.prepareStatement(itemInsert)) {
                        ins.setInt(1, orderId);
                        ins.setInt(2, itemId);
                        ins.setInt(3, qty);
                        ins.setDouble(4, subtotal);
                        ins.executeUpdate();
                    }
                } else {
                    System.out.println("Item unavailable or invalid ID.");
                }
            }
        }

        String updateTotal = "UPDATE orders SET total_amount = ? WHERE order_id = ?";
        try (PreparedStatement pstmt = conn.prepareStatement(updateTotal)) {
            pstmt.setDouble(1, grandTotal);
            pstmt.setInt(2, orderId);
            pstmt.executeUpdate();
        }
        System.out.printf("Order #%d placed successfully! Total Amount: Rs. %.2f\n", orderId, grandTotal);
    }

    private static void updateOrderStatus(Connection conn, Scanner sc) throws SQLException {
        System.out.print("Enter Order ID: ");
        int orderId = sc.nextInt();
        sc.nextLine();
        System.out.print("Enter New Status (Placed / Preparing / Completed / Cancelled): ");
        String status = sc.nextLine();

        String sql = "UPDATE orders SET order_status = ? WHERE order_id = ?";
        try (PreparedStatement pstmt = conn.prepareStatement(sql)) {
            pstmt.setString(1, status);
            pstmt.setInt(2, orderId);
            int rows = pstmt.executeUpdate();
            System.out.println(rows > 0 ? "Order status updated!" : "Order ID not found.");
        }
    }

    private static void generateReports(Connection conn) throws SQLException {
        System.out.println("\n--- Popular Menu Items ---");
        String popSql = "SELECT m.item_name, SUM(oi.quantity) AS sold FROM order_items oi " +
                        "JOIN menu m ON oi.item_id = m.item_id GROUP BY m.item_name ORDER BY sold DESC";
        try (Statement stmt = conn.createStatement(); ResultSet rs = stmt.executeQuery(popSql)) {
            while (rs.next()) {
                System.out.println(rs.getString("item_name") + " -> Sold: " + rs.getInt("sold"));
            }
        }

        System.out.println("\n--- Daily Sales Summary ---");
        String salesSql = "SELECT DATE(order_date) AS dt, SUM(total_amount) AS rev FROM orders " +
                          "WHERE order_status != 'Cancelled' GROUP BY DATE(order_date)";
        try (Statement stmt = conn.createStatement(); ResultSet rs = stmt.executeQuery(salesSql)) {
            while (rs.next()) {
                System.out.printf("Date: %s | Revenue: Rs. %.2f\n", rs.getDate("dt"), rs.getDouble("rev"));
            }
        }
    }
}