from flask import Blueprint, jsonify, request
from app.auth import require_auth
from app.db import get_db_connection, close_db_connection
import os

users_bp = Blueprint('users', __name__)

@users_bp.route('/protected-info', methods=['GET'])
@require_auth
def protected_info():
    return jsonify({
        "message": request.user['email'],
        "user_id": request.user['sub']
    })

@users_bp.route('/users', methods=['POST'])
@require_auth
def create_user():
    data = request.json
    name = data.get('name')
    role = data.get('role')
    u_id = request.user['sub']
    email = request.user['email']

    if not name or not role:
        return jsonify({"error": "Name and role are required."}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO Users (u_id, Email, Name, Role)
            VALUES (%s, %s, %s, %s);
        """, (u_id, email, name, role))
        conn.commit()
        return jsonify({"message": "User created successfully!"}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
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

SUPABASE_PROJECT_ID = 'pnvmksvuwvvrdqqjsyqf'
SUPABASE_API_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
SUPABASE_AUTH_URL = 'https://pnvmksvuwvvrdqqjsyqf.supabase.co/auth/v1/admin/users'

@users_bp.route('/users/<uuid:u_id>', methods=['DELETE'])
@require_auth
def delete_user(u_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("DELETE FROM Users WHERE U_Id = %s;", (u_id,))
        conn.commit()
        headers = {
            "apikey": SUPABASE_API_KEY,
            "Authorization": f"Bearer {SUPABASE_API_KEY}"
        }
        res = request.delete(f"{SUPABASE_AUTH_URL}/{u_id}", headers=headers)

        if res.status_code == 204:
            return jsonify({"message": "User successfully deleted"}), 200
        else:
            return jsonify({
                "warning": "Deletion error",
                "details": res.text
            }), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400

    finally:
        cur.close()
        close_db_connection(conn)

@users_bp.route('/users/<uuid:c_id>/preferences', methods=['PUT'])
@require_auth
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