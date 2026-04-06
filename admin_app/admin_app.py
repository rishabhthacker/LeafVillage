from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
import mysql.connector
from sqlalchemy import text
from werkzeug.security import generate_password_hash, check_password_hash
from models import db


app = Flask(__name__)
app.secret_key = "your_secret_key"
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Rudra28@127.0.0.1/your_database_name'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db = SQLAlchemy(app)

# Database connection
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Rudra28",
        database="your_database_name"
    )


# Subadmin Register
@app.route('/subadmin/register', methods=['GET', 'POST'])
def subadmin_register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Corrected hashing method
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)

        db = get_db_connection()
        cursor = db.cursor()
        try:
            cursor.execute(
                "INSERT INTO subadmins (username, email, password) VALUES (%s, %s, %s)",
                (username, email, hashed_password)
            )
            db.commit()
            flash("Registration successful! You can now log in.")
            return redirect(url_for('subadmin_login'))
        except Exception as e:
            db.rollback()
            flash(f"Error: {e}")
        finally:
            cursor.close()
            db.close()

    return render_template('subadmin_register.html')


# Subadmin Login
@app.route('/subadmin/login', methods=['GET', 'POST'])
def subadmin_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Validate input fields
        if not email or not password:
            flash("Email and password are required.", "danger")
            return render_template('subadmin_login.html')

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        try:
            # Fetch the subadmin record from the database
            cursor.execute("SELECT * FROM subadmins WHERE email = %s", (email,))
            subadmin = cursor.fetchone()

            if subadmin:
                # Verify password
                if check_password_hash(subadmin['password'], password):
                    # Set session variables
                    session['subadmin_id'] = subadmin['subadmin_id']
                    session['subadmin_username'] = subadmin['username']

                    flash("Login successful!", "success")
                    return redirect(url_for('subadmin_dashboard'))
                else:
                    flash("Invalid password. Please try again.", "danger")
            else:
                flash("No subadmin found with this email. Please check your credentials.", "danger")

        except Exception as e:
            flash(f"An error occurred while processing your request: {e}", "danger")
        finally:
            cursor.close()
            db.close()

    return render_template('subadmin_login.html')


# Subadmin Dashboard
@app.route('/subadmin/dashboard')
def subadmin_dashboard():
    if 'subadmin_id' not in session:
        flash("You must log in first!")
        return redirect(url_for('subadmin_login'))
    return render_template('subadmin_dashboard.html', username=session['subadmin_username'])


# Sub-Admin: Add Product
@app.route('/subadmin/add_product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        product_name = request.form['product_name']
        description = request.form['description']
        price = request.form['price']
        stock_quantity = request.form['stock_quantity']  
        category = request.form['category']
        subcategory = request.form['subcategory']
        image_url = request.form['image_url']
        steps_to_grow = request.form['steps_to_grow']

        db = get_db_connection()
        cursor = db.cursor()
        try:
            cursor.execute(
                """INSERT INTO products 
                (product_name, description, price, stock_quantity, category, subcategory, image_url, steps_to_grow) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (product_name, description, price, stock_quantity, category, subcategory, image_url, steps_to_grow)
            )
            db.commit()
            flash("Product added successfully!")
        except Exception as e:
            db.rollback()
            flash(f"Error: {e}")
        finally:
            cursor.close()
            db.close()
        return redirect(url_for('manage_products'))

    return render_template('add_product.html')


# Sub-Admin: Manage Products (List, Edit, Delete)
@app.route('/subadmin/manage_products', methods=['GET'])
def manage_products():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM products ORDER BY product_id DESC")  # Ensures new products appear first
        products = cursor.fetchall()
    except Exception as e:
        products = []
        flash(f"Error fetching products: {e}")
    finally:
        cursor.close()
        db.close()
    return render_template('manage_products.html', products=products)


# Subadmin Message
@app.route('/subadmin/view_messages')
def view_messages():
    if 'subadmin_id' not in session:
        flash("You must log in first!")
        return redirect(url_for('subadmin_login'))

    # Assuming you are using SQLAlchemy for the Message model
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM messages ORDER BY created_at DESC")
        messages = cursor.fetchall()
    except Exception as e:
        messages = []
        flash(f"Error fetching messages: {e}")
    finally:
        cursor.close()
        db.close()

    return render_template('view_messages.html', messages=messages)


# Manage Orders
from sqlalchemy.sql import text  # Ensure this is imported

@app.route('/subadmin/orders', methods=['GET'])
def subadmin_orders():
    if 'subadmin_id' not in session:
        flash('Please log in to access this page.', 'danger')
        return redirect(url_for('subadmin_login'))

    try:
        # SQL Query to fetch orders
        query = text("""
            SELECT 
                o.user_id, 
                u.username, 
                u.email, 
                oi.product_id, 
                p.product_name, 
                p.price, 
                oi.quantity, 
                u.address
            FROM 
                orders o
            JOIN 
                order_items oi ON o.order_id = oi.order_id
            JOIN 
                products p ON oi.product_id = p.product_id
            JOIN 
                user u ON o.user_id = u.user_id
            ORDER BY 
                o.order_id DESC
        """)

        # Execute the query
        orders = db.session.execute(query).fetchall()

        # Convert results to a list of dictionaries
        order_data = [
            {
                "user_id": order.user_id,
                "username": order.username,
                "email": order.email,
                "product_id": order.product_id,
                "product_name": order.product_name,
                "price": order.price,
                "quantity": order.quantity,
                "address": order.address,
            }
            for order in orders
        ]

        # Render the template
        return render_template('subadmin_orders.html', orders=order_data)

    except Exception as e:
        flash(f"Error loading orders: {e}", 'danger')
        return redirect(url_for('subadmin_dashboard'))


# Sub-Admin: Delete Product
@app.route('/subadmin/delete_product/<int:product_id>', methods=['POST', 'DELETE'])
def delete_product(product_id):
    db = get_db_connection()
    cursor = db.cursor()
    try:
        cursor.execute("DELETE FROM products WHERE product_id = %s", (product_id,))
        db.commit()
        flash("Product deleted successfully!")
    except Exception as e:
        flash(f"Error deleting product: {e}")
    finally:
        cursor.close()
        db.close()
    return redirect(url_for('manage_products'))


# Sub-Admin: Update Product
@app.route('/subadmin/update_product/<int:product_id>', methods=['GET', 'POST'])
def update_product(product_id):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        # Fetch the product to edit
        cursor.execute("SELECT * FROM products WHERE product_id = %s", (product_id,))
        product = cursor.fetchone()
        if not product:
            flash("Product not found!")
            return redirect(url_for('manage_products'))

        if request.method == 'POST':
            # Update the product details
            product_name = request.form.get('product_name')
            image_url = request.form.get('image_url')
            price = request.form.get('price')
            stock_quantity = request.form.get('stock')
            description = request.form.get('description')
            steps_to_grow = request.form.get('steps_to_grow')

            # Validate that required fields are filled
            if not (product_name and image_url and price and stock_quantity and description):
                flash("All fields except 'steps_to_grow' are required!")
                return render_template('update_product.html', product=product)

            cursor.execute(
                """UPDATE products
                   SET product_name=%s, image_url=%s, price=%s, stock_quantity=%s, description=%s, steps_to_grow=%s
                   WHERE product_id=%s""",
                (product_name, image_url, price, stock_quantity, description, steps_to_grow, product_id)
            )
            db.commit()
            flash("Product updated successfully!")
            return redirect(url_for('manage_products'))
    except Exception as e:
        db.rollback()  # Rollback any changes in case of an error
        flash(f"Error: {e}")
    finally:
        cursor.close()
        db.close()

    return render_template('update_product.html', product=product)


# User: View Products
@app.route('/products/<category>/<subcategory>')
def view_products_by_category(category, subcategory):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT * FROM products WHERE category = %s AND subcategory = %s", 
            (category, subcategory)
        )
        products = cursor.fetchall()
    except Exception as e:
        products = []
        flash(f"Error fetching products: {e}")
    finally:
        cursor.close()
        db.close()
    return render_template('products.html', products=products, category=category, subcategory=subcategory)


# User: Add to Cart
@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    quantity = int(request.form['quantity'])

    db = get_db_connection()
    cursor = db.cursor()
    try:
        cursor.execute(
            "INSERT INTO cart (user_id, product_id, quantity) VALUES (%s, %s, %s)",
            (1, product_id, quantity)  # Replace 1 with session user_id
        )
        db.commit()
        flash("Product added to cart!")
    except Exception as e:
        flash(f"Error adding to cart: {e}")
    finally:
        cursor.close()
        db.close()
    return redirect(url_for('view_products'))


# User: Buy Now
@app.route('/buy_now/<int:product_id>', methods=['GET'])
def buy_now(product_id):
    flash("Thank you for your purchase!")
    return redirect(url_for('view_products'))


# Sub-Admin: Logout
@app.route('/subadmin/logout')
def subadmin_logout():
    session.pop('subadmin_id', None)
    session.pop('subadmin_username', None)
    flash("Logged out successfully!")
    return redirect(url_for('subadmin_login'))


# Run the app
if __name__ == "__main__":
    app.run(debug=True)
