from flask import Blueprint, jsonify, request
from app.db import get_db_connection, close_db_connection
from datetime import date, timedelta

transactions_bp = Blueprint('transaction', __name__)

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
            SELECT t.T_Id, b.B_Id, b.Title, b.Genre, t.TransactionDate, t.Due_Date, m.IsLibrary, t.Returned_At
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
                "transaction_id": str(row[0]),
                "book_id": str(row[1]),
                "book_title": row[2],
                "genre": row[3],
                "date": row[4],
                "due_date": row[5],
                "is_library": row[6],
                "returned_at": row[7]
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
        
        cur.execute("""
                    SELECT B_Id 
                    FROM Transactions
                    WHERE T_Id = %s;
                """, (transaction_id,))
        result = cur.fetchone()
        if not result:
            return jsonify({"error": "Transaction not found"}), 404
        b_id = result[0]
        
        cur.execute("""
            UPDATE Books
            SET Stock = Stock + 1
            WHERE B_Id = %s;
        """, (b_id,))

        conn.commit()
        return jsonify({"message": "Book returned and stock is updated."}), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        cur.close()
        close_db_connection(conn)

def transaction_fine(due_date, returned_at):
    effective_return = returned_at

    if effective_return <= due_date:
        return 0

    days_late = (effective_return - due_date).days
    return 2 + days_late

@transactions_bp.route('/transactions/<uuid:transaction_id>/fine', methods=['GET'])
def transaction_fine(transaction_id):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT t.Due_Date, t.returned_at
            FROM Transactions t
            JOIN Books b ON t.B_Id = b.B_Id
            JOIN Sells s ON b.B_Id = s.B_Id
            JOIN Merchants m ON s.M_Id = m.M_Id
            WHERE t.T_Id = %s AND m.IsLibrary = TRUE;
        """, (str(transaction_id),))

        result = cur.fetchone()
        if not result:
            return jsonify({"fine": 0, "message": "No fine"}), 200
        due_date, returned_at = result
        fine = transaction_fine(due_date, returned_at)

        return jsonify({
            "transaction_id": str(transaction_id),
            "due_date": due_date.isoformat() if due_date else None,
            "returned_at": returned_at.isoformat() if returned_at else None,
            "fine": fine
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400

    finally:
        cur.close()
        close_db_connection(conn)

@transactions_bp.route('/transactions/<uuid:user_id>/fine', methods=['GET'])
def total_fines(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT t.Due_Date, t.returned_at
            FROM Transactions t
            JOIN Books b ON t.B_Id = b.B_Id
            JOIN Sells s ON b.B_Id = s.B_Id
            JOIN Merchants m ON s.M_Id = m.M_Id
            WHERE m.IsLibrary = TRUE AND (
                (t.returned_at IS NULL AND t.Due_Date < CURRENT_DATE) OR
                (t.returned_at IS NOT NULL AND t.returned_at > t.Due_Date)
            ) AND t.C_Id = %s;
        """, (str(user_id),))
        transactions = cur.fetchall()

        total_fine = sum(
            transaction_fine(due_date=row[0], returned_at=row[1])
            for row in transactions
        )
        cur.execute("""
            UPDATE Customers
            SET Fines = %s
            WHERE C_Id = %s;
        """, (total_fine, str(user_id)))

        conn.commit()
        return jsonify({"fine": total_fine}), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400

    finally:
        cur.close()
        close_db_connection(conn)