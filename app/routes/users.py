from flask import Blueprint, jsonify, request
from app.db import get_db_connection, close_db_connection

users_bp = Blueprint('users', __name__)

@users_bp.route('/users', methods=['GET'])
def get_users():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT U_Id, Name, Email, Role FROM Users;")
    users = cur.fetchall()
    cur.close()
    close_db_connection(conn)

    users_list = [
        {"id": str(user[0]), "name": user[1], "email": user[2], "role": user[3]}
        for user in users
    ]
    return jsonify(users_list)

@users_bp.route('/users', methods=['POST'])
def create_user():
    data = request.json
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("INSERT INTO Users (Name, Email, Password, Role) VALUES (%s, %s, %s, %s) RETURNING U_Id;",
                    (data['name'], data['email'], data['password'], data['role']))
        user_id = cur.fetchone()[0]
        conn.commit()
        return jsonify({"message": "User created successfully!", "user_id": str(user_id)}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        cur.close()
        close_db_connection(conn)
