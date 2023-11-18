import wtforms.validators
from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import os
import requests

TMDB_KEY = os.environ.get("TMDB_API_KEY")
TMDB_URL = "https://api.themoviedb.org/3/search/movie"

print(TMDB_KEY)

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)

# CREATE DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies.db'
db = SQLAlchemy()
db.init_app(app)


# CREATE TABLE
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)


with app.app_context():
    db.create_all()


class RateMovieForm(FlaskForm):
    rating = StringField('Your Rating Out of 10 e.g. 7.5')
    review = StringField('Your Review')
    done = SubmitField('Done')


class FindMovieForm(FlaskForm):
    title = StringField('Movie Title', validators=[DataRequired()])
    submit = SubmitField('Add Movie')


@app.route("/")
def home():
    all_movies = db.session.execute(db.select(Movie).order_by(Movie.ranking)).scalars()
    return render_template("index.html", movies=all_movies)


@app.route("/edit", methods=["GET", "POST"])
def rate_movie():
    edit_rating_form = RateMovieForm()
    movie_id = request.args.get("id")
    movie = db.get_or_404(Movie, movie_id)
    if edit_rating_form.validate_on_submit():
        movie.rating = float(edit_rating_form.rating.data)
        movie.review = edit_rating_form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", movie=movie, rating_form=edit_rating_form)


@app.route("/delete", methods=["GET", "POST"])
def delete_movie():
    movie_id = request.args.get("id")
    movie = db.get_or_404(Movie, movie_id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/add", methods=["GET", "POST"])
def add_movie():
    find_movie_form = FindMovieForm()
    if find_movie_form.validate_on_submit():
        movie_title = find_movie_form.title.data
        response = requests.get(url=TMDB_URL, params={"api_key": TMDB_KEY, "query": movie_title})
        movie_data = response.json()['results']
        return render_template('select.html', data=movie_data)
    return render_template("add.html", find_form=find_movie_form)


if __name__ == '__main__':
    app.run(debug=True)
