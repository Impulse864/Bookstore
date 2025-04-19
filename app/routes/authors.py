from flask import Blueprint, jsonify, request
from app.db import get_db_connection, close_db_connection

authors_bp = Blueprint('authors', __name__)

@authors_bp.route('/authors', methods=['GET'])
def get_authors():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT A_Id, FirstName, LastName FROM Authors;")
    authors = cur.fetchall()
    cur.close()
    close_db_connection(conn)

    authors_list = [
        {"first name": author[1], "last name": author[2]}
        for author in authors
    ]
    return jsonify(authors_list)

@authors_bp.route('/authors', methods=['POST'])
def create_author():
    data = request.json
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO Authors (Name) VALUES (%s) RETURNING A_Id;", (data['name'],))
        author_id = cur.fetchone()[0]
        conn.commit()
        return jsonify({"message": "Author created", "author_id": str(author_id)}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        cur.close()
        close_db_connection(conn)
        
@authors_bp.route('/authors/<author_id>', methods=['DELETE'])
def delete_author(author_id):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM Authors WHERE A_Id = %s;", (author_id,))
        conn.commit()
        return jsonify({"message": "Author deleted"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        cur.close()
        close_db_connection(conn)
