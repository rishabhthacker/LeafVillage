from multiprocessing import connection
import os
from flask import Flask, Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import Order, User, db, ContactMessage, OrderItem
from sqlalchemy import text
from flask import jsonify
from decimal import Decimal
import razorpay
from datetime import datetime
import re


# App Configurations
app = Flask(__name__)
app.secret_key = "your_secret_key"
app.config['UPLOAD_FOLDER'] = 'static/uploads/profile_pictures'


# Razorpay API Key
RAZORPAY_KEY_ID = 'rzp_test_jV9RYIDmszkAoD'
RAZORPAY_SECRET = '5Dyo0NmGynvUXvctByBkruwR'


razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_SECRET))


# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Blueprint for modularity
user_bp = Blueprint('user', __name__)


UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.before_request
def log_request_info():
    app.logger.info(f"Request URL: {request.url} Method: {request.method}")


# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Rudra28@127.0.0.1/your_database_name'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)


# User Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')

        if not username or not password or not email:
            flash("All fields are required!", "danger")
            return redirect(url_for('register'))

        # Hash the password
        hashed_password = generate_password_hash(password)

        try:
            query = text("INSERT INTO user (username, password, email) VALUES (:username, :password, :email)")
            db.session.execute(query, {"username": username, "password": hashed_password, "email": email})
            db.session.commit()
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for('login'))
        except Exception as e:
            flash(f"Registration failed: {e}", "danger")
            return redirect(url_for('register'))

    return render_template('login-register.html', form_type='register')


# User Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            flash("Both fields are required!", "danger")
            return redirect(url_for('login'))

        try:
            query = text("SELECT * FROM user WHERE username = :username")
            user = db.session.execute(query, {"username": username}).fetchone()

            if user and check_password_hash(user.password, password):  # Check the hashed password
                # Initialize session with user details
                session['username'] = user.username
                session['user_email'] = user.email
                flash("Login successful!", "success")
                return redirect(url_for('home'))
            else:
                flash("Invalid username or password.", "danger")
                return redirect(url_for('login'))
        except Exception as e:
            flash(f"Login failed: {e}", "danger")
            return redirect(url_for('login'))

    return render_template('login-register.html', form_type='login')


# User Logout
@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))


# Home Route
@app.route('/')
def home():
    if 'username' in session:
        return render_template('index.html', username=session['username'])
    return redirect(url_for('login'))


# View Product By Category
@app.route('/products/<category>/<subcategory>', methods=['GET'])
def view_products_by_category(category, subcategory):
    sort_by = request.args.get('sort_by', 'default')  # Default sorting order

    try:
        # Construct the SQL query based on the sort_by parameter
        base_query = """
            SELECT * FROM products WHERE category = :category AND subcategory = :subcategory
        """

        if sort_by == "price_high_to_low":
            base_query += " ORDER BY price DESC"
        elif sort_by == "price_low_to_high":
            base_query += " ORDER BY price ASC"
        elif sort_by == "name_a_to_z":
            base_query += " ORDER BY product_name ASC"
        elif sort_by == "name_z_to_a":
            base_query += " ORDER BY product_name DESC"

        # Execute the query
        query = text(base_query)
        products = db.session.execute(query, {"category": category, "subcategory": subcategory}).fetchall()

        # Prepare the product list
        products_list = [
            {
                "product_id": product.product_id,
                "product_name": product.product_name,
                "price": product.price,
                "description": product.description,
                "image_url": product.image_url,
                "stock_quantity": product.stock_quantity,
            }
            for product in products
        ]

    except Exception as e:
        print(f"Error fetching products: {e}")
        flash(f"Error fetching products: {e}")
        products_list = []

    return render_template(
        'products.html',
        products=products_list,
        category=category,
        subcategory=subcategory,
        sort_by=sort_by
    )


# Example Navigation Integration (Optional)
@app.route('/navigate')
def navigate():
    # Example usage of view_products_by_category
    return redirect(url_for('view_products_by_category', category='Plants', subcategory='Indoor'))


# User: View All Products
# Updates in view_all_products route
@app.route('/products')
def view_all_products():
    try:
        query = text("SELECT * FROM products")
        products = db.session.execute(query).fetchall()

        # Format products for the template
        products_list = [
            {
                "product_id": product.product_id,
                "product_name": product.product_name,
                "price": product.price,
                "description": product.description,
                "image_url": product.image_url,
                "stock_quantity": product.stock_quantity,
            }
            for product in products
        ]

    except Exception as e:
        flash(f"Error fetching products: {e}", "danger")
        products_list = []

    return render_template('products.html', products=products_list)


# Particular Product
@app.route('/product/<int:product_id>')
def product_details(product_id):
    try:
        query = text("SELECT * FROM products WHERE product_id = :product_id")
        product = db.session.execute(query, {"product_id": product_id}).fetchone()

        if not product:
            flash("Product not found.")
            return redirect(url_for('view_all_products'))

        product_details = {
            "product_id": product.product_id,
            "product_name": product.product_name,
            "price": product.price,
            "description": product.description,
            "image_url": product.image_url,
            "stock_quantity": product.stock_quantity,
            "steps_to_grow": product.steps_to_grow,
        }

    except Exception as e:
        flash(f"Error fetching product details: {e}")
        return redirect(url_for('view_all_products'))

    return render_template('product_details.html', product=product_details)


# About Us Page
@app.route('/about')
def about_us():
    return render_template('about_us.html')


# Contact Us Page 
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        user_name = request.form['name']
        user_email = request.form['email']
        user_message = request.form['message']

        try:
            # Use SQLAlchemy to insert the contact message
            message = ContactMessage(
                user_name=user_name,
                user_email=user_email,
                user_message=user_message,
            )
            db.session.add(message)
            db.session.commit()

            # Flash a success message
            flash("Your message has been sent successfully!", "success")
        except Exception as e:
            db.session.rollback()

            # Flash an error message
            flash(f"Error submitting message: {e}", "danger")

    return render_template('contact_us.html')


# My Account
@app.route('/my_account', methods=['GET', 'POST'])
def my_account():
    # Check if user is logged in
    if 'username' not in session:
        flash('Please log in first.')
        return redirect(url_for('login'))

    # Fetch the current user based on session username
    username = session['username']
    user = User.query.filter_by(username=username).first()

    if not user:
        flash('User not found.')
        return redirect(url_for('login'))

    if request.method == 'POST':
        try:
            # Update user details
            user.first_name = request.form.get('first_name', user.first_name)
            user.last_name = request.form.get('last_name', user.last_name)
            user.phone = request.form.get('phone', user.phone)
            user.gender = request.form.get('gender', user.gender)
            user.address = request.form.get('address', user.address)  # Update address field

            # Handle profile picture upload
            file = request.files.get('profile_picture')
            if file and file.filename:
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                user.profile_picture = f'uploads/{filename}'

            # Save changes to the database
            db.session.commit()
            flash('Profile updated successfully!')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {e}', 'danger')

        return redirect(url_for('my_account'))

    # Render the my_account.html template
    return render_template('my_account.html', user=user)


# Add Product to Cart
@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if 'username' not in session:
        return jsonify({"status": "error", "message": "Please log in to add items to your cart."}), 403

    try:
        product_id = request.form.get('product_id')
        quantity = int(request.form.get('quantity', 1))
        username = session['username']

        # Check if the product exists
        product_query = text("SELECT * FROM products WHERE product_id = :product_id")
        product = db.session.execute(product_query, {"product_id": product_id}).fetchone()

        if not product:
            return jsonify({"status": "error", "message": "Product not found."}), 404

        # Check if the product is already in the cart
        cart_query = text("SELECT * FROM cart WHERE username = :username AND product_id = :product_id")
        cart_item = db.session.execute(cart_query, {"username": username, "product_id": product_id}).fetchone()

        if cart_item:
            # Update the quantity
            update_query = text("""
                UPDATE cart SET quantity = quantity + :quantity 
                WHERE username = :username AND product_id = :product_id
            """)
            db.session.execute(update_query, {"quantity": quantity, "username": username, "product_id": product_id})
        else:
            # Add new item to cart
            insert_query = text("""
                INSERT INTO cart (username, product_id, quantity) 
                VALUES (:username, :product_id, :quantity)
            """)
            db.session.execute(insert_query, {"username": username, "product_id": product_id, "quantity": quantity})

        db.session.commit()
        return jsonify({"status": "success", "message": "Product added to cart!"})

    except Exception as e:
        db.session.rollback() 
        return jsonify({"status": "error", "message": str(e)}), 500


# View Cart
@app.route('/cart', methods=['GET', 'POST'])
def view_cart():
    if 'username' not in session:
        flash("Please log in to view your cart.", "warning")
        return redirect(url_for('login'))

    try:
        username = session['username']
        query = text("""
            SELECT c.product_id, p.product_name, p.price, p.image_url, c.quantity 
            FROM cart c 
            JOIN products p ON c.product_id = p.product_id 
            WHERE c.username = :username
        """)
        cart_items = db.session.execute(query, {"username": username}).fetchall()

        # Process the cart items
        cart = [
            {
                "product_id": item.product_id,
                "product_name": item.product_name,
                "price": item.price,
                "image_url": item.image_url,
                "quantity": item.quantity,
                "total_price": item.price * item.quantity,
            }
            for item in cart_items
        ]
        total = sum(item["total_price"] for item in cart)

        if request.method == 'POST':
            # Redirect to payment page with total amount
            return redirect(url_for('payment', total=total))

        return render_template('cart.html', cart=cart, total=total)

    except Exception as e:
        flash(f"Error fetching cart: {e}", "danger")
        return redirect(url_for('home'))


# Remove Item from Cart
@app.route('/remove_from_cart/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    if 'username' not in session:
        flash("Please log in to remove items from your cart.", "warning")
        return redirect(url_for('login'))

    try:
        username = session['username']
        delete_query = text("DELETE FROM cart WHERE username = :username AND product_id = :product_id")
        db.session.execute(delete_query, {"username": username, "product_id": product_id})
        db.session.commit()
        flash("Item removed from cart!", "success")
        return redirect(url_for('view_cart'))
    except Exception as e:
        db.session.rollback()
        flash(f"Error removing item from cart: {e}", "danger")
        return redirect(url_for('view_cart'))


# Blog 1
@app.route('/blog1')
def blog1():
    return render_template('blog1.html')


# Blog 2
@app.route('/blog2')
def blog2():
    return render_template('blog2.html')


# Blog 3
@app.route('/blog3')
def blog3():
    return render_template('blog3.html')


# Payment Page
@app.route('/payment', methods=['GET', 'POST'])
def payment():
    if 'username' not in session:
        flash("Please log in to proceed with payment.", "warning")
        return redirect(url_for('login'))

    try:
        username = session['username']

        # Query total price and product details from the cart
        query = text("""
            SELECT p.product_name, p.price, c.quantity, 
                   (p.price * c.quantity) AS total_price
            FROM cart c
            JOIN products p ON c.product_id = p.product_id
            WHERE c.username = :username
        """)
        result = db.session.execute(query, {"username": username}).fetchall()

        # Calculate total price and prepare cart items
        total_price = 0
        cart_items = []
        for row in result:
            cart_items.append({
                "product_name": row.product_name,
                "price": row.price,
                "quantity": row.quantity
            })
            total_price += row.total_price

        if total_price == 0:
            flash("Your cart is empty. Add some items to proceed.", "warning")
            return redirect(url_for('view_cart'))

        if request.method == 'POST':
            # Razorpay expects the amount in paise
            amount_in_paise = int(total_price * 100)

            # Create Razorpay order
            order_data = {
                "amount": amount_in_paise,
                "currency": "INR",
                "payment_capture": 1,  # Auto capture payment
            }
            razorpay_order = razorpay_client.order.create(order_data)

            # Debugging logs
            print("✅ Razorpay Order Created:", razorpay_order)

            # Store order ID in session
            session['razorpay_order_id'] = razorpay_order['id']
            session['total_price'] = total_price

            # Redirect to Razorpay checkout page
            return jsonify({
                "order_id": razorpay_order['id'],
                "amount": total_price,
                "redirect_url": url_for('payment_success')
            })

        return render_template(
            'payment.html', 
            total_price=total_price, 
            cart_items=cart_items,  # Pass cart items to the template
            order_id=session.get('razorpay_order_id', ''), 
            razorpay_key_id=RAZORPAY_KEY_ID  # Pass Razorpay Key
        )

    except Exception as e:
        flash(f"Error processing payment: {e}", "danger")
        return redirect(url_for('view_cart'))


# Payment Successful Confirmation
@app.route('/payment_success', methods=['POST'])
def payment_success():
    try:
        data = request.get_json()
        payment_id = data.get('razorpay_payment_id')
        razorpay_order_id = data.get('razorpay_order_id')
        signature = data.get('razorpay_signature')

        # Verify payment signature
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        }

        try:
            razorpay_client.utility.verify_payment_signature(params_dict)

            # Get username from session
            username = session.get('username')
            if not username:
                return jsonify({"error": "❌ User not logged in. Payment cannot be processed."}), 400

            # Remove items from the cart
            delete_query = text("DELETE FROM cart WHERE username = :username")
            db.session.execute(delete_query, {"username": username})
            db.session.commit()

            # Store payment details in the session
            session['razorpay_order_id'] = razorpay_order_id
            session['razorpay_payment_id'] = payment_id
            session['total_price'] = session.get('total_price', 0)

            flash("✅ Payment successful! Items removed from your cart.", "success")
            return jsonify({"redirect_url": url_for('order_confirmation')})

        except Exception as e:
            return jsonify({"error": f"❌ Payment verification failed: {e}"}), 400

    except Exception as e:
        return jsonify({"error": f"❌ Error processing payment: {e}"}), 400


# Order Confirmation Page
@app.route('/order_confirmation')
def order_confirmation():
    # Retrieve payment details from the session
    razorpay_order_id = session.get('razorpay_order_id')
    payment_id = session.get('razorpay_payment_id')
    total_price = session.get('total_price')

    if not razorpay_order_id or not payment_id:
        flash("No payment information found. Please try again.", "warning")
        return redirect(url_for('view_cart'))

    # Debugging: Print to ensure the session contains the order ID
    print("✅ Order Confirmation - Razorpay Order ID:", razorpay_order_id)

    # Clear session data after order confirmation
    session.pop('razorpay_order_id', None)
    session.pop('razorpay_payment_id', None)
    session.pop('total_price', None)

    return render_template(
        'order_confirmation.html',
        razorpay_order_id=razorpay_order_id,
        payment_id=payment_id,
        total_price=total_price
    )


# Razorpay Callback
@app.route('/payment/callback', methods=['POST'])
def payment_callback():
    try:
        # Get Razorpay payment details
        payment_id = request.form.get('razorpay_payment_id')
        order_id = request.form.get('razorpay_order_id')
        signature = request.form.get('razorpay_signature')

        # Verify payment signature
        params_dict = {
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature,
        }
        try:
            razorpay_client.utility.verify_payment_signature(params_dict)
        except razorpay.errors.SignatureVerificationError:
            flash("Payment verification failed.", "danger")
            # Update payment status as Failed
            order = Order.query.filter_by(razorpay_order_id=order_id).first()
            order.payment_status = "Failed"
            db.session.commit()
            return redirect(url_for('view_cart'))

        # Update payment details in database
        order = Order.query.filter_by(razorpay_order_id=order_id).first()
        order.razorpay_payment_id = payment_id
        order.razorpay_signature = signature
        order.payment_status = "Paid"
        db.session.commit()

        flash("Payment successful!", "success")
        return redirect(url_for('home'))

    except Exception as e:
        flash(f"Error processing payment: {e}", "danger")
        return redirect(url_for('view_cart'))


# Webhook Route(Related to payment)
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        webhook_data = request.get_json()

        if webhook_data.get('event') == 'payment.captured':
            razorpay_order_id = webhook_data['payload']['payment']['entity']['order_id']

            # Update order status in the database
            order = Order.query.filter_by(order_status="Pending", razorpay_order_id=razorpay_order_id).first()
            if order:
                order.order_status = "Completed"
                order.payment_method = "Complete"
                db.session.commit()
                print("Order status updated for order ID:", order.order_id)

        return '', 200
    except Exception as e:
        print(f"Error in webhook: {e}")
        return '', 400


# Order being saved in database
@app.route('/place_order', methods=['POST'])
def place_order():
    if 'user_id' not in session:
        flash("Please log in to place an order.", "danger")
        return redirect(url_for('login'))

    user_id = session['user_id']
    cart = session.get('cart', [])  # Assuming you store cart items in the session

    if not cart:
        flash("Your cart is empty. Add some products first.", "danger")
        return redirect(url_for('view_cart'))

    try:
        db = get_db_connection()
        cursor = db.cursor()

        # Step 1: Insert the order into the `orders` table
        cursor.execute("""
            INSERT INTO orders (user_id, order_date) VALUES (%s, NOW())
        """, (user_id,))
        order_id = cursor.lastrowid  # Get the newly created order ID

        # Step 2: Insert items into the `order_items` table
        for item in cart:
            product_id = item['product_id']
            quantity = item['quantity']
            cursor.execute("""
                INSERT INTO order_items (order_id, product_id, quantity)
                VALUES (%s, %s, %s)
            """, (order_id, product_id, quantity))

        db.commit()  # Save all changes to the database

        # Clear the cart
        session['cart'] = []
        flash("Order placed successfully!", "success")
        return redirect(url_for('order_summary', order_id=order_id))

    except Exception as e:
        db.rollback()  # Roll back changes if something goes wrong
        flash(f"Error placing order: {e}", "danger")
        return redirect(url_for('view_cart'))

    finally:
        cursor.close()
        db.close()


# Our Plantation
@app.route('/our_plantation')
def our_plantation():
    return render_template('our_plantation.html')


# Our Vision
@app.route('/our_vision')
def our_vision():
    return render_template('our_vision.html')


# Our From The Farmers
@app.route('/from_the_farmers')
def from_the_farmers():
    return render_template('from_the_farmers.html')


# Our Customer FAQs
@app.route('/customer_faqs')
def customer_faqs():
    return render_template('customer_faqs.html')


# Our Privacy Policy
@app.route('/privacy_policy')
def privacy_policy():
    return render_template('privacy_policy.html')


# Whatever you do, don't remove this code!!(To make the code run)
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")
    app.run(debug=True)