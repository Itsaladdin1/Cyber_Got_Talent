from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
import os
from modules.News import news_bp, db
from modules.vote import vote_bp, initialize_database
from modules.ticket import ticket_bp, init_db

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'you-will-never-guess'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cybernews.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/news_images/'

# Define database paths
tickets_db_path = os.path.join(app.instance_path, 'tickets.db')
vote_db_path = os.path.join(app.instance_path, 'vote.db')

# Ensure the instance folder exists
os.makedirs(app.instance_path, exist_ok=True)

# Initialize SQLAlchemy
db.init_app(app)

class RouteSetup:
    def __init__(self, app):
        self.app = app
        self.setup_routes()

    def setup_routes(self):
        @self.app.route('/')
        def index():
            return render_template('index.html')

        @self.app.route('/about')
        def about():
            return render_template('cyber2023/html/all-in/home-about.html')

        @self.app.route('/show')
        def show():
            return render_template('cyber2023/html/all-in/show.html')

        @self.app.route('/table-uno')
        def table_uno():
            return render_template('cyber2023/html/tournament/tournament-table-uno-2023.html')

        @self.app.route('/ticket-info')
        def tickets_info():
            return render_template('ticket/tickets_info.html')

        @self.app.route('/team')
        def team():
            return render_template('cyber2023/html/all-in/Team.html')

        @self.app.route('/champions')
        def champions():
            return render_template('cyber2023/html/all-in/winners-table.html')

        @self.app.route('/reklam')
        def reklam():
            return render_template('reklam.html')

        @self.app.route('/contact')
        def contact():
            return render_template('cyber2023/html/all-in/contact.html')

        @self.app.route('/table-winner')
        def table_winner():
            return render_template('cyber2023/html/tournament/tournament-W.html')

        @self.app.route('/host')
        def host():
            return render_template('cyber2023/html/all-in/hosting.html')

        @self.app.route('/votes')
        def votes():
            return render_template('vote.html')

# Register the blueprints
app.register_blueprint(news_bp, url_prefix='/news')
app.register_blueprint(vote_bp, url_prefix='/')
app.register_blueprint(ticket_bp, url_prefix='/')

# Database Initialization
tables_created = False

@app.before_request
def create_tables():
    global tables_created
    if not tables_created:
        with app.app_context():
            db.create_all()  # Create tables for the SQLAlchemy database
            # Ensure you are using the correct database path
            init_db(tickets_db_path)  # Initialize the tickets database using the correct path in instance
            initialize_database(vote_db_path)  # Initialize the vote database
            tables_created = True

if __name__ == '__main__':
    RouteSetup(app)
    app.run(debug=True)
