from flask import Blueprint, jsonify
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
