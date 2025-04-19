from flask import Blueprint, jsonify, request
from app.db import get_db_connection, close_db_connection

books_bp = Blueprint('books', __name__)

@books_bp.route('/books', methods=['GET'])
def get_books():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT B_Id, Title, Genre, PublishYear, Rating FROM Books;")
    books = cur.fetchall()
    cur.close()
    close_db_connection(conn)

    books_list = [
        {"id": str(book[0]), "title": book[1], "genre": book[2], "year": book[3], "rating": float(book[4])}
        for book in books
    ]
    return jsonify(books_list)

@books_bp.route('/books', methods=['POST'])
def create_book():
    data = request.json
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO Books (Title, Genre, PublishYear, Rating, Price, Stock)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING B_Id;
        """, (data['title'], data['genre'], data['publish_year'], data['rating'], data['price'], data['stock']))
        book_id = cur.fetchone()[0]

        cur.execute("INSERT INTO Sells (M_Id, B_Id) VALUES (%s, %s);", (data['merchant_id'], book_id))

        conn.commit()
        return jsonify({"message": "Book created", "book_id": str(book_id)}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        cur.close()
        close_db_connection(conn)

@books_bp.route('/books/<uuid:b_id>', methods=['DELETE'])
def delete_book(book_id):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM Books WHERE B_Id = %s;", (book_id,))
        conn.commit()
        return jsonify({"message": "Book deleted"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        cur.close()
        close_db_connection(conn)

@books_bp.route('/books/filter', methods=['POST'])
def filter_books():
    data = request.json
    genre = data.get('genre')
    author = data.get('author')
    max_price = data.get('max_price')

    query = """
        SELECT DISTINCT b.B_Id, b.Title, b.Genre, b.Price, b.Rating
        FROM Books b
        LEFT JOIN Written w ON b.B_Id = w.B_Id
        LEFT JOIN Authors a ON w.A_Id = a.A_Id
        WHERE (%s IS NULL OR b.Genre = %s) AND (%s IS NULL OR a.Name = %s) AND (%s IS NULL OR b.Price <= %s);
    """

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(query, (genre, genre, author, author, max_price, max_price))
        books = cur.fetchall()
        return jsonify([{
            "id": str(row[0]),
            "title": row[1],
            "genre": row[2],
            "price": row[3],
            "rating": row[4]
        } for row in books]), 200
    finally:
        cur.close()
        close_db_connection(conn)

@books_bp.route('/books/<uuid:book_id>/subtract_stock', methods=['POST'])
def subtract_stock(book_id):
    data = request.json
    amount = data.get('amount', 1)

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE Books SET Stock = Stock - %s WHERE B_Id = %s;", (amount, book_id))
        conn.commit()
        return jsonify({"message": f"Stock decreased by {amount} for book {book_id}"}), 200
    finally:
        cur.close()
        close_db_connection(conn)
        
@books_bp.route('/books/<uuid:book_id>/add_stock', methods=['POST'])
def add_book_stock(book_id):
    data = request.json
    amount = data.get('amount', 1)

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE Books SET Stock = Stock + %s WHERE B_Id = %s;", (amount, book_id))
        conn.commit()
        return jsonify({"message": f"Stock increased by {amount} for book {book_id}"}), 200
    finally:
        cur.close()
        close_db_connection(conn)
