from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from slugify import slugify

# Create a blueprint for the news section
news_bp = Blueprint('news', __name__, template_folder='templates')

# Initialize the database
db = SQLAlchemy()

# Models
class Month(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    def __repr__(self):
        return f'<Month {self.name}>'

class NewsArticle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    published_date = db.Column(db.DateTime, default=datetime.utcnow)
    publisher = db.Column(db.String(100), nullable=False)
    image = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    month_id = db.Column(db.Integer, db.ForeignKey('month.id'), nullable=False)
    month = db.relationship('Month', backref=db.backref('articles', lazy=True))

    def __repr__(self):
        return f'<NewsArticle {self.title}>'

    def generate_slug(self):
        if self.title:
            self.slug = slugify(self.title)

# Routes
@news_bp.route('/news')
def index():
    latest_articles = NewsArticle.query.order_by(NewsArticle.published_date.desc()).limit(4).all()
    months = Month.query.all()
    return render_template('news.html', latest_articles=latest_articles, months=months)

@news_bp.route('/news/<slug>')
def news_detail(slug):
    article = NewsArticle.query.filter_by(slug=slug).first_or_404()
    return render_template('news_detail.html', article=article)

@news_bp.route('/month/<month_name>')
def news_by_month(month_name):
    # Ensure the month_name is case insensitive
    month = Month.query.filter(db.func.lower(Month.name) == month_name.lower()).first_or_404()
    articles = NewsArticle.query.filter_by(month_id=month.id).all()
    return render_template('news_by_month.html', month=month, articles=articles)

@news_bp.route('/admin/news', methods=['GET', 'POST'])
def add_news():
    if request.method == 'POST':
        title = request.form['title']
        publisher = request.form['publisher']
        content = request.form['content']
        month_name = request.form['month']
        image_file = request.files['image']

        # Ensure the upload directory exists
        upload_folder = news_bp.config['UPLOAD_FOLDER']
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)

        # Save the image
        if image_file:
            image_path = os.path.join(upload_folder, image_file.filename)
            image_file.save(image_path)

        # Get or create the month
        month = Month.query.filter_by(name=month_name).first()
        if not month:
            month = Month(name=month_name)
            db.session.add(month)
            db.session.commit()

        # Create a new article and generate slug
        new_article = NewsArticle(
            title=title,
            publisher=publisher,
            content=content,
            image=image_file.filename,
            month_id=month.id
        )
        new_article.generate_slug()
        db.session.add(new_article)
        db.session.commit()

        flash('News article added successfully!')
        return redirect(url_for('news.index'))

    return render_template('admin_add_news.html')
