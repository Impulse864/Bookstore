from flask import Flask
from app.routes.books import books_bp
from app.routes.users import users_bp
from app.routes.authors import authors_bp
from app.routes.transactions import transactions_bp

app = Flask(__name__)

# Register blueprints (routes)
app.register_blueprint(books_bp)
app.register_blueprint(users_bp)
app.register_blueprint(authors_bp)
app.register_blueprint(transactions_bp)

if __name__ == '__main__':
    app.run(debug=True)