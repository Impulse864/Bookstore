from flask import Blueprint, jsonify, request
from app.db import get_db_connection, close_db_connection

transactions_bp = Blueprint('transaction', __name__)

from datetime import date, timedelta

@transactions_bp.route('/transactions', methods=['POST'])
def create_transaction():
    data = request.json
    b_id = data['b_id']
    c_id = data['c_id']

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT m.IsLibrary
            FROM Books b
            JOIN Sells s ON b.B_Id = s.B_Id
            JOIN Merchants m ON s.M_Id = m.M_Id
            WHERE b.B_Id = %s;
        """, (b_id,))
        result = cur.fetchone()

        if result is None:
            return jsonify({"error": "Book not found"}), 404

        is_library = result[0]
        transaction_date = date.today()
        due_date = transaction_date + timedelta(days=7) if is_library else None

        cur.execute("""
            INSERT INTO Transactions (B_Id, C_Id, TransactionDate, Due_Date)
            VALUES (%s, %s, %s, %s)
            RETURNING T_Id;
        """, (b_id, c_id, transaction_date, due_date))

        transaction_id = cur.fetchone()[0]
        conn.commit()

        return jsonify({
            "message": "Transaction created.",
            "transaction_id": str(transaction_id),
            "due_date": due_date.isoformat() if due_date else None
        }), 201

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        cur.close()
        close_db_connection(conn)


@transactions_bp.route('/transactions/<uuid:customer_id>', methods=['GET'])
def get_transaction_history(customer_id):
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT t.T_Id, b.Title, b.Genre, t.TransactionDate
            FROM Transactions t
            JOIN Books b ON t.B_Id = b.B_Id
            JOIN Sells s ON b.B_Id = s.B_Id
            JOIN Merchants m ON s.M_Id = m.M_Id
            WHERE t.C_Id = %s
            ORDER BY t.TransactionDate DESC;
        """, (str(customer_id),))
        history = cur.fetchall()

        result = [
            {
                "transaction\_id": str(row[0]),
                "book_title": row[1],
                "genre": row[2],
                "date": row[3]
            } for row in history
        ]

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cur.close()
        close_db_connection(conn)


@transactions_bp.route('/transactions/<uuid:customer_id>/overdue', methods=['GET'])
def get_overdue_books(customer_id):
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT t.T_Id, b.Title, t.TransactionDate, t.Due_Date
            FROM Transactions t
            JOIN Books b ON t.B_Id = b.B_Id
            JOIN Sells s ON b.B_Id = s.B_Id
            JOIN Merchants m ON s.M_Id = m.M_Id
            WHERE t.C_Id = %s AND m."IsLibrary" = TRUE AND t.Due_Date < CURRENT_DATE;
        """, (str(customer_id),))
        overdue = cur.fetchall()

        result = [
            {
                "transaction_id": str(row[0]),
                "book_title": row[1],
                "borrowed_on": row[2],
                "due_date": row[3]
            } for row in overdue
        ]

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cur.close()
        close_db_connection(conn)
        
@transactions_bp.route('/transactions/<uuid:transaction_id>/return', methods=['PUT'])
def return_book(transaction_id):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE Transactions
            SET returned_at = CURRENT_DATE
            WHERE T_Id = %s;
        """, (transaction_id,))
        conn.commit()
        return jsonify({"message": "Book marked as returned."}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        cur.close()
        close_db_connection(conn)

@transactions_bp.route('/transactions/<uuid:user_id>/fine', methods=['GET'])
def calculate_fine(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT COUNT(*) * 2 AS total_fine
            FROM Transactions t
            JOIN Books b ON t.Book_Id = b.Book_Id
            JOIN Merchants m ON b.Merchant_Id = m.Merchant_Id
            WHERE m.IsLibrary = TRUE AND (
                (t.returned_at IS NULL AND t.due_date < CURRENT_DATE) OR
                (t.returned_at IS NOT NULL AND t.returned_at > t.due_date)) AND t.C_Id = %s;
        """, (user_id,))
        fine = '2'
        return jsonify({"fine": fine}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        cur.close()
        close_db_connection(conn)

        cur.close()
        close_db_connection(conn)
