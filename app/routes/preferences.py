from flask import Blueprint, jsonify, request
from app.db import get_db_connection, close_db_connection

preferences_bp = Blueprint('preferences', __name__)

@preferences_bp.route('/users/<uuid:c_id>/preferences', methods=['PUT'])
def update_preferences(c_id):
    data = request.json
    c_id = data.get('c_id')
    fav_authors = data.get('fav_authors')
    fav_genres = data.get('fav_genres')
    fav_books = data.get('fav_books')

    print(f"INFO: {c_id}, {type(fav_authors)}, {fav_genres}, {fav_books}")

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO Preferences (C_Id, FavAuthors, FavGenres, FavBooks)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (C_Id) DO UPDATE
            SET FavAuthors = EXCLUDED.FavAuthors, FavGenres = EXCLUDED.FavGenres, FavBooks = EXCLUDED.FavBooks;
        """, (c_id, f'{{"{fav_authors}"}}', f'{{"{fav_genres}"}}', f'{{"{fav_books}"}}'))
        conn.commit()
        return jsonify({"message": "Preferences updated."}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        cur.close()
        close_db_connection(conn)