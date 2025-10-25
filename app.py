from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector

app = Flask(__name__)
app.secret_key = 'some_secret_key'

db_config = {
    'host': 'localhost',
    'user': 'eatrushd_eatrush',
    'password': '6!6Sgk1KP5s+Md', 
    'database': 'eatrushd_eatrush', 
    'port': 3306
}

def get_db_connection():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except mysql.connector.Error as err:
        flash(f"Error: {err}", 'error')
        return None

# Fungsi untuk membuat tabel jika belum ada
def create_table():
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT
            )
        """)
        conn.commit()
        cursor.close()
        conn.close()

# Pastikan tabel sudah dibuat saat aplikasi pertama kali dijalankan
create_table()

@app.route('/', methods=['GET', 'POST'])
def index():
    conn = get_db_connection()
    if not conn:
        return "Database connection error.", 500

    cursor = conn.cursor(dictionary=True)

    # Logika untuk mencari data
    search_query = request.args.get('search', '')
    
    # Logika untuk mengurutkan data
    sort_by = request.args.get('sort_by', 'id')
    order = request.args.get('order', 'asc')
    
    # Pastikan order hanya 'asc' atau 'desc'
    if order.lower() not in ['asc', 'desc']:
        order = 'asc'
        
    query = f"SELECT * FROM items WHERE name LIKE %s OR description LIKE %s ORDER BY {sort_by} {order}"
    cursor.execute(query, (f"%{search_query}%", f"%{search_query}%"))
    
    items = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('index.html', items=items, search_query=search_query, sort_by=sort_by, order=order)

@app.route('/add', methods=['POST'])
def add_item():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']

        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            query = "INSERT INTO items (name, description) VALUES (%s, %s)"
            cursor.execute(query, (name, description))
            conn.commit()
            cursor.close()
            conn.close()
            flash('Item berhasil ditambahkan!', 'success')
    return redirect(url_for('index'))

@app.route('/update/<int:id>', methods=['POST'])
def update_item(id):
    name = request.form['name']
    description = request.form['description']
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        query = "UPDATE items SET name = %s, description = %s WHERE id = %s"
        cursor.execute(query, (name, description, id))
        conn.commit()
        cursor.close()
        conn.close()
        flash('Item berhasil diperbarui!', 'success')
    return redirect(url_for('index'))

@app.route('/delete/<int:id>', methods=['POST'])
def delete_item(id):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        query = "DELETE FROM items WHERE id = %s"
        cursor.execute(query, (id,))
        conn.commit()
        cursor.close()
        conn.close()
        flash('Item berhasil dihapus!', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
