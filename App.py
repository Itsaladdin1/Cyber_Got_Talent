from flask import render_template

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

        @self.app.route('/news')
        def news():
            return render_template('cyber2023/html/all-in/news.html')
        
        @self.app.route('/show')
        def show():
            return render_template('cyber2023/html/all-in/show.html')
        
        @self.app.route('/table-uno')
        def table_uno():
            return render_template('cyber2023/html/tournament/tournament-table-uno-2023.html')
        
        @self.app.route('/tickets')
        def tickets():
            return render_template('tickets/tickets.html')
        
        @self.app.route('/team')
        def team():
            return render_template('cyber2023/html/all-in/Team.html')

        @self.app.route('/champions')
        def champions():
            return render_template('cyber2023/html/all-in/winners-table.html')
        
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