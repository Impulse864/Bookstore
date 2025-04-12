from flask import Blueprint, jsonify
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