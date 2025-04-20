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
            SELECT m.IsLibrary, b.stock
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

        print(f"Book id: {b_id}, Customer: {c_id}")

        cur.execute("""
            INSERT INTO Transactions (c_id, b_id, Transaction_Date, Due_Date)
            VALUES (%s, %s, %s, %s)
            RETURNING T_Id;
        """, (c_id, b_id, transaction_date, due_date))

        transaction_id = cur.fetchone()[0]

        cur.execute("""
            UPDATE Books
            SET Stock = Stock - 1
            WHERE B_Id = %s; """, (b_id,))


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

    data = request.json
    customer_id = data.get('user_id')
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT t.T_Id, b.B_Id, b.Title, b.Genre, t.Transaction_Date, t.Due_Date, m.IsLibrary, t.return_date
            FROM Transactions t
            JOIN Books b ON t.B_Id = b.B_Id
            JOIN Sells s ON b.B_Id = s.B_Id
            JOIN Merchants m ON s.M_Id = m.M_Id
            WHERE t.C_Id = %s
            ORDER BY t.Transaction_Date DESC;
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
    data = request.json
    customer_id = data.get('user_id')
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT t.T_Id, b.Title, t.Transaction_Date, t.Due_Date
            FROM Transactions t
            JOIN Books b ON t.B_Id = b.B_Id
            JOIN Sells s ON b.B_Id = s.B_Id
            JOIN Merchants m ON s.M_Id = m.M_Id
            WHERE t.C_Id = %s AND m.IsLibrary = TRUE AND t.Due_Date < CURRENT_DATE AND t.return_date IS NULL;
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
    data = request.json
    transaction_id = data.get('transaction_id')
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE Transactions
            SET return_date = CURRENT_DATE
            WHERE T_Id = %s;
        """, (transaction_id,))

        print("Updated transactions")
        
        cur.execute("""
                    SELECT B_Id 
                    FROM Transactions
                    WHERE T_Id = %s;
                """, (transaction_id,))
        result = cur.fetchone()
        if not result:
            return jsonify({"error": "Transaction not found"}), 404
        b_id = result[0]

        print("Got book id")
        
        cur.execute("""
            UPDATE Books
            SET Stock = Stock + 1
            WHERE B_Id = %s;
        """, (b_id,))

        print("updated stock")

        conn.commit()
        return jsonify({"message": "Book returned and stock is updated."}), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        cur.close()
        close_db_connection(conn)

@transactions_bp.route('/transactions/<uuid:customer_id>/return_all', methods=['PUT'])
def return_all(customer_id):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT t.T_Id, t.B_Id
            FROM Transactions t
            JOIN Books b ON t.B_Id = b.B_Id
            JOIN Sells s ON b.B_Id = s.B_Id
            JOIN Merchants m ON s.M_Id = m.M_Id
            WHERE t.C_Id = %s AND m.IsLibrary = TRUE AND t.returned_at IS NULL;
        """, (str(customer_id),))
        
        transactions = cur.fetchall()

        if not transactions:
            return jsonify({"message": "No borrowed books to return."}), 200

        for t_id, b_id in transactions:
            cur.execute("""
                UPDATE Transactions
                SET returned_at = CURRENT_DATE
                WHERE T_Id = %s;
            """, (t_id,))
            cur.execute("""
                UPDATE Books
                SET Stock = Stock + 1
                WHERE B_Id = %s;
            """, (b_id,))

        conn.commit()
        return jsonify({"message": f"Returned {len(transactions)} borrowed book(s)."}), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400

    finally:
        cur.close()
        close_db_connection(conn)

def calculate_transaction_fine(due_date, returned_at):
    print("calculating fine")
    effective_return = returned_at

    if effective_return <= due_date:
        return 0

    days_late = (effective_return - due_date).days

    print(f"fine is {2 + days_late}")
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

@transactions_bp.route('/transactions/<uuid:user_id>/total_fines', methods=['GET'])
def total_fines(user_id):
    data = request.json
    user_id = data.get('user_id')
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT t.Due_Date, t.return_date
            FROM Transactions t
            JOIN Books b ON t.B_Id = b.B_Id
            JOIN Sells s ON b.B_Id = s.B_Id
            JOIN Merchants m ON s.M_Id = m.M_Id
            WHERE m.IsLibrary = TRUE AND (
                (t.return_date IS NULL AND t.Due_Date < CURRENT_DATE) OR
                (t.return_date IS NOT NULL AND t.return_date > t.Due_Date)
            ) AND t.C_Id = %s;
        """, (str(user_id),))
        transactions = cur.fetchall()

        total_fine = 0
        #for row in transactions:
        #    fine = calculate_transaction_fine(due_date=row[0], returned_at=row[1])
        #    total_fine += fine

        total_fine = 2 * len(transactions)

        print(f"calculated fines {total_fine}")

        cur.execute("""
            UPDATE Customers
            SET Fines = %s
            WHERE C_Id = %s;
        """, (total_fine, str(user_id)))

        print(f"updated fines")

        conn.commit()
        return jsonify({"fine": total_fine}), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400

    finally:
        cur.close()
        close_db_connection(conn)