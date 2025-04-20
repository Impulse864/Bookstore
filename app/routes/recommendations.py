from flask import Blueprint, jsonify, request
from app.db import get_db_connection, close_db_connection

recommendations_bp = Blueprint('recommendations', __name__)

@recommendations_bp.route('/books/recommend/<user_id>', methods=['GET'])
def recommend_books(user_id):
    data = request.json
    user_id = data.get('user_id')
    query = """
        SELECT DISTINCT b.B_Id, b.Title, b.Genre, b.Price, b.Rating
        FROM Books b
        LEFT JOIN Transactions t ON b.B_Id = t.B_Id AND t.c_Id = %s
        JOIN Preferences c ON c.C_Id = %s
        LEFT JOIN Written w ON b.B_Id = w.B_Id
        JOIN Authors a ON w.a_id = a.a_id
        WHERE t.T_Id IS NULL AND (b.Genre = ANY(c.favgenres) OR b.Title != ANY(c.favbooks) OR a.full_name = ANY(c.favauthors));
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(query, (user_id, user_id))
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
