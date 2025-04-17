from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash
import os
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
        hashed_password = generate_password_hash(data['password'])
        cur.execute("""
            INSERT INTO Users (Name, Email, Password, Role)
            VALUES (%s, %s, %s, %s) RETURNING U_Id;
        """, (data['name'], data['email'], hashed_password, data['role']))
        user_id = cur.fetchone()[0]
        conn.commit()
        return jsonify({"message": "User created successfully!", "user_id": str(user_id)}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        cur.close()
        close_db_connection(conn)

@users_bp.route('/users/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM Users WHERE Email = %s;", (email,))
        user = cur.fetchone()

        if user and check_password_hash(user[3], password):
            return jsonify({"id": str(user[0]), "name": user[1], "email": user[2],"role": user[4]}), 200
        else:
            return jsonify({'error': 'Invalid email or password'}), 401

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        close_db_connection(conn)
