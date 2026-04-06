from flask import app
from admin_app.admin_app import get_db_connection

@app.route('/test_db')
def test_db():
    try:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("SELECT DATABASE();")
        database_name = cursor.fetchone()
        cursor.close()
        db.close()
        return f"Connected to database: {database_name}"
    except Exception as e:
        return f"Database connection error: {e}"
