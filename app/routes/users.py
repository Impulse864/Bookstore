from flask import Blueprint, jsonify, request
from app.db import get_db_connection, close_db_connection

users_bp = Blueprint('users', __name__)

@users_bp.route('/users', methods=['POST'])
def create_user():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role')

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT 1 FROM Users WHERE Email = %s;", (email,))
        if cur.fetchone():
            return jsonify({"error": "Email already registered."})
        
        cur.execute("""
            INSERT INTO Users (Name, Email, Password, Role)
            VALUES (%s, %s, %s, %s)
            RETURNING U_Id;
        """, (name, email, password, role))
        u_id = cur.fetchone()[0]

        if role == 'customer':
            cur.execute("INSERT INTO Customers (C_Id) VALUES (%s);", (u_id,))
        elif role == 'merchant':
            cur.execute("INSERT INTO Merchants (M_Id) VALUES (%s);", (u_id,))

        conn.commit()
        return jsonify({"message": "User created successfully", "user_id": str(u_id)}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        cur.close()
        close_db_connection(conn)

@users_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT U_Id, Name, Email, Password, Role FROM Users
            WHERE Email = %s;
        """, (email,))
        user = cur.fetchone()
        if not user or user[3] != password:
            return jsonify({"error": "Invalid email or password"}), 401

        return jsonify({
            "message": "Login successful",
            "user_id": str(user[0]),
            "name": user[1],
            "email": user[2],
            "role": user[4]
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        close_db_connection(conn)

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

@users_bp.route('/users/<uuid:u_id>', methods=['PUT'])
def update_user_info(u_id):
    data = request.json
    name = data.get('name')
    role = data.get('role')
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE Users
            SET Name = %s, Role = %s
            WHERE U_Id = %s;
        """, (name, role, u_id))
        conn.commit()
        return jsonify({"message": "User info updated successfully!"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        cur.close()
        close_db_connection(conn)

@users_bp.route('/users/<uuid:u_id>', methods=['DELETE'])
def delete_user(u_id):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM Users WHERE U_Id = %s;", (u_id,))
        conn.commit()
        return jsonify({"message": "User deleted successfully."}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        cur.close()
        close_db_connection(conn)

@users_bp.route('/users/<uuid:c_id>/preferences', methods=['PUT'])
def update_preferences(c_id):
    data = request.json
    fav_authors = data.get('fav_authors', [])
    fav_genres = data.get('fav_genres', [])
    fav_books = data.get('fav_books', [])

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO Preferences (C_Id, FavAuthors, FavGenres, FavBooks)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (C_Id) DO UPDATE
            SET FavAuthors = EXCLUDED.FavAuthors, FavGenres = EXCLUDED.FavGenres, FavBooks = EXCLUDED.FavBooks;
        """, (c_id, fav_authors, fav_genres, fav_books))
        conn.commit()
        return jsonify({"message": "Preferences updated."}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        cur.close()
        close_db_connection(conn)
