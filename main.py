import wtforms.validators
from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import os
import requests


TMDB_KEY = os.environ.get('TMDB_API_KEY')
TMDB_URL = "https://api.themoviedb.org/3/search/movie"
TMDB_ID_URL = "https://api.themoviedb.org/3/movie/"
TMDB_IMAGE_URL = "https://image.tmdb.org/t/p/w500/"

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
    """
    Renders the homepage with a list of all the movies in the movies' database.
    Movies are ordered by the rating and assigned a rank, 1-100 with 1 being the highest rated movie
     """
    result = db.session.execute(db.select(Movie).order_by(Movie.rating.desc()))
    all_movies = result.scalars().all()
    for i in range(len(all_movies)):
        all_movies[i].ranking = i + 1
    db.session.commit()
    return render_template("index.html", movies=all_movies)


@app.route("/edit", methods=["GET", "POST"])
def rate_movie():
    """ Renders page with a flask form allowing you to edit the rating and review of a movie in the movies database """
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
    """ Pressing the delete button will remove chosen movie from the database """
    movie_id = request.args.get("id")
    movie = db.get_or_404(Movie, movie_id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/add", methods=["GET", "POST"])
def add_movie():
    """
    add_movie takes an input of a film name then makes a request to The Movie DataBase retrieving all the
    movies with the given name and then renders select.html with a list off all results
    """
    find_movie_form = FindMovieForm()
    if find_movie_form.validate_on_submit():
        movie_title = find_movie_form.title.data
        response = requests.get(url=TMDB_URL, params={"api_key": TMDB_KEY, "query": movie_title})
        movie_data = response.json()['results']
        return render_template('select.html', data=movie_data)
    return render_template("add.html", find_form=find_movie_form)


@app.route("/find")
def find_movie():
    """
    Once you select the movie you want from select.html this function retrieves the movie id then renders
    edit.html allowing you to leave a rating and review for the movie before it is displayed on the homepage
    """
    movie_id = request.args.get('id')
    movie_api_url = f'{TMDB_ID_URL}{movie_id}'
    if movie_id:
        chosen_movie = requests.get(url=movie_api_url, params={"api_key": TMDB_KEY, "language": 'en-US'}).json()
        image_path = chosen_movie['belongs_to_collection']['poster_path']
        movie_image_url = f"{TMDB_IMAGE_URL}{image_path}"
        new_movie = Movie(
            title=chosen_movie['title'],
            description=chosen_movie['overview'],
            year=chosen_movie['release_date'].split('-')[0],
            img_url=movie_image_url,
        )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for('rate_movie', id=new_movie.id))


if __name__ == '__main__':
    app.run(debug=True)
