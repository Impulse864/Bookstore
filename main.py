from flask import Flask
from app.routes.authors import authors_bp
from app.routes.books import books_bp
from app.routes.preferences import preferences_bp
from app.routes.recommendations import recommendations_bp
# from app.routes.sells import sells_bp
from app.routes.transactions import transactions_bp
from app.routes.users import users_bp


app = Flask(__name__)

app.register_blueprint(authors_bp)
app.register_blueprint(books_bp)
app.register_blueprint(preferences_bp)
app.register_blueprint(recommendations_bp)
# app.register_blueprint(sells_bp)
app.register_blueprint(transactions_bp)
app.register_blueprint(users_bp)

if __name__ == '__main__':
    app.run(debug=True)