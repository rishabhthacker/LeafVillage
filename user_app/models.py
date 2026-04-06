from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# User Table
class User(db.Model):
    __tablename__ = 'user'
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    phone = db.Column(db.String(15), unique=True, nullable=False)  # Fixed duplicate phone column
    first_name = db.Column(db.String(100), nullable=True)
    last_name = db.Column(db.String(100), nullable=True)
    gender = db.Column(db.Enum('male', 'female'), nullable=True)
    profile_picture = db.Column(db.String(255), nullable=True)
    address = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<User {self.username}>"  # Fixed self.name to self.username


# Product Table
class Product(db.Model):
    __tablename__ = 'products'
    product_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    stock_quantity = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"<Product {self.name}>"


# Order Item Table
class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.order_id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.product_id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    # Define relationships
    order = db.relationship('Order', backref=db.backref('order_items', lazy=True))
    product = db.relationship('Product', backref=db.backref('order_items', lazy=True))

    def __init__(self, order_id, product_id, quantity):
        self.order_id = order_id
        self.product_id = product_id
        self.quantity = quantity


# Shopping Cart Table
class ShoppingCart(db.Model):
    __tablename__ = 'shopping_cart'
    cart_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)  # Fixed table reference
    product_id = db.Column(db.Integer, db.ForeignKey('products.product_id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"<ShoppingCart Cart ID: {self.cart_id}>"


# Payment Table
class Payment(db.Model):
    __tablename__ = 'payment'
    payment_id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.order_id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_method = db.Column(db.Enum('PayPal', 'Cash on Delivery'), nullable=False)
    payment_status = db.Column(db.Enum('Pending', 'Completed', 'Failed'), nullable=False)


# Shipping Table
class Shipping(db.Model):
    __tablename__ = 'shipping'
    shipping_id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.order_id'), nullable=False)
    shipping_address = db.Column(db.Text, nullable=False)
    shipping_status = db.Column(db.Enum('Pending', 'In Transit', 'Delivered'), nullable=False)


# Admin Table
class Admin(db.Model):
    __tablename__ = 'admin'
    admin_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)  # Removed unique=True


# Sub-Admin Table
class SubAdmin(db.Model):
    __tablename__ = 'sub_admin'
    sub_admin_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)  # Removed unique=True


# Message Table
class ContactMessage(db.Model):
    __tablename__ = 'messages'
    message_id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(100), nullable=False)
    user_email = db.Column(db.String(150), nullable=False)
    user_message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())


# Orders model
class Order(db.Model):
    __tablename__ = 'orders'

    order_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, nullable=False)  # Foreign key to the user's table (if exists)
    total_price = db.Column(db.Numeric(10, 2), nullable=False)
    shipping_address = db.Column(db.Text, nullable=False)
    order_status = db.Column(
        db.Enum('Pending', 'Shipped', 'Delivered', 'Cancelled', name='order_status_enum'),
        nullable=False,
        default='Pending'
    )
    payment_status = db.Column(
        db.Enum('Pending', 'Complete', 'Failed', name='payment_status_enum'),
        nullable=False,
        default='Pending'
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, user_id, total_price, shipping_address, order_status='Pending', payment_status='Pending'):
        self.user_id = user_id
        self.total_price = total_price
        self.shipping_address = shipping_address
        self.order_status = order_status
        self.payment_status = payment_status

    def __repr__(self):
        return f"<Order {self.order_id}>"