
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3, math
from database import init_db

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key'

MOVIES_PER_PAGE = 5

init_db()

def get_all_users():
    with sqlite3.connect('movies.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT user_name FROM favorite_genres")
        return [r[0] for r in cur.fetchall()]

def get_all_genres():
    with sqlite3.connect('movies.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT genre FROM movies_table")
        rows = [r[0] for r in cur.fetchall() if r[0]]
    s = set()
    for entry in rows:
        for g in entry.split(','):
            g = g.strip()
            if g: s.add(g)
    return sorted(s)

def get_all_countries():
    with sqlite3.connect('movies.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT countries FROM movies_table")
        rows = [r[0] for r in cur.fetchall() if r[0]]
    return sorted(rows)

def get_all_movies():
    with sqlite3.connect('movies.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM movies_table")
        return cur.fetchall()

def get_rated_ids(user):
    with sqlite3.connect('movies.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT movie_id FROM rated_movies_table WHERE user_name=?", (user,))
        return [r[0] for r in cur.fetchall()]

def movie_matches_genres(mg_str, fav_genres):
    mg = [g.strip().lower() for g in mg_str.split(',') if g.strip()]
    return any(fg.lower() in mg for fg in fav_genres)

def are_similar_users(user_a: str, user_b: str) -> bool:
    conn = sqlite3.connect('movies.db')
    cur = conn.cursor()
    cur.execute("SELECT movie_id, user_rating FROM rated_movies_table WHERE user_name=?", (user_a,))
    a = {r[0]: r[1] for r in cur.fetchall()}
    cur.execute("SELECT movie_id, user_rating FROM rated_movies_table WHERE user_name=?", (user_b,))
    b = {r[0]: r[1] for r in cur.fetchall()}
    conn.close()

    common = set(a) & set(b)
    if not common:
        return False
    same = sum(1 for m in common if a[m] == b[m])
    return same >= len(common) / 2

def get_similar_users(user: str) -> list:
    conn = sqlite3.connect('movies.db')
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT user_name FROM rated_movies_table WHERE user_name!=?", (user,))
    others = [r[0] for r in cur.fetchall()]
    conn.close()

    return [u for u in others if are_similar_users(user, u)]

def get_collaborative_movies(candidates, matched, exclude_ids, similar_users):
    if not similar_users:
        return []

    conn = sqlite3.connect('movies.db')
    cur = conn.cursor()
    collab = []

    for m in candidates:
        mid = m[0]
        if m in matched or (exclude_ids and mid in exclude_ids):
            continue

        ph = ",".join("?" for _ in similar_users)
        sql = f"""
            SELECT user_rating FROM rated_movies_table
            WHERE movie_id=? AND user_name IN ({ph})
        """
        cur.execute(sql, [mid, *similar_users])
        ratings = [r[0] for r in cur.fetchall()]

        if not ratings:
            continue

        likes = sum(1 for r in ratings if r)
        if likes >= len(ratings) / 2:
            collab.append(m)

    conn.close()
    return collab

def get_movies(genres, exclude_ids=None, limit=None):
    if not genres:
        return []

    placeholders = " OR ".join(["genre LIKE ?"] * len(genres))
    params = [f"%{g}%" for g in genres]
    sql = f"SELECT * FROM movies_table WHERE ({placeholders})"
    if exclude_ids:
        ph_ex = ",".join("?" for _ in exclude_ids)
        sql += f" AND id NOT IN ({ph_ex})"
        params += exclude_ids

    conn = sqlite3.connect('movies.db')
    cur = conn.cursor()
    cur.execute(sql, params)
    candidates = cur.fetchall()
    conn.close()

    matched = [m for m in candidates if movie_matches_genres(m[2], genres)]

    current = session.get('user')
    similar = get_similar_users(current)
    collab = get_collaborative_movies(candidates, matched, exclude_ids, similar)

    full_list = matched + collab

    return full_list[:limit] if limit is not None else full_list

def sort_movies_by_rating(movies, descending=True):
    return sorted(movies, key=lambda m: m[7] or 0, reverse=descending)

def sort_movies_by_year(movies, descending=False):
    return sorted(movies, key=lambda m: m[3] or 0, reverse=descending)

@app.route('/')
def index():
    users = get_all_users()
    return render_template('login.html', users=users)

@app.route('/login', methods=['POST'])
def login():
    user = request.form['user_name']
    session.clear()
    session['user'] = user
    session['shown_ids'] = []
    with sqlite3.connect('movies.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT genre FROM favorite_genres WHERE user_name=?", (user,))
        genres = [r[0] for r in cur.fetchall()]
    if genres:
        session['genres'] = genres
        return redirect(url_for('home'))
    session['genres'] = []
    return redirect(url_for('select_genres'))

@app.route('/new_user')
def new_user():
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register():
    user = request.form['user_name']
    if user in get_all_users():
        return render_template('register.html', error="Пользователь с таким именем уже существует")
    session.clear()
    session['user'] = user
    session['shown_ids'] = []
    return redirect(url_for('select_genres'))

@app.route('/select_genres')
def select_genres():
    genres = get_all_genres()
    return render_template('select_genres.html', genres=genres)

@app.route('/save_genres', methods=['POST'])
def save_genres():
    user = session['user']
    chosen = request.form.getlist('genres')
    with sqlite3.connect('movies.db') as conn:
        cur = conn.cursor()
        for g in chosen:
            cur.execute(
                "INSERT OR IGNORE INTO favorite_genres (user_name, genre) VALUES (?,?)",
                (user, g)
            )
        conn.commit()
    session['genres'] = chosen
    return redirect(url_for('rate_movies'))

@app.route('/rate_movies')
def rate_movies():
    user = session['user']
    genres = session.get('genres', [])
    rated = get_rated_ids(user)
    movies = get_movies(genres, exclude_ids=rated, limit=10)
    return render_template('rate_movies.html', movies=movies)

@app.route('/submit_ratings', methods=['POST'])
def submit_ratings():
    user = session['user']
    for key, val in request.form.items():
        if key.startswith('movie_') and val in ('like','dislike'):
            mid = int(key.split('_',1)[1])
            with sqlite3.connect('movies.db') as conn:
                cur = conn.cursor()
                cur.execute(
                    "INSERT OR IGNORE INTO rated_movies_table (user_name, movie_id) VALUES (?,?)",
                    (user, mid)
                )
                conn.commit()
            session['shown_ids'].append(mid)
    return redirect(url_for('home'))


@app.route('/home')
def home():
    user = session.get('user')
    if not user:
        return redirect(url_for('index'))

    genres = session.get('genres', [])
    rated = get_rated_ids(user)
    shown = session.get('shown_ids', [])
    exclude = list(set(rated + shown))
    all_movies = get_movies(genres, exclude_ids=exclude, limit=100)

    sort_by = request.args.get('sort_by', 'rating')
    sorted_movies = sort_movies_by_rating(all_movies, descending=True)
    if sort_by == 'year_asc':
        sorted_movies = sort_movies_by_year(all_movies, descending=False)
    elif sort_by == 'year_desc':
        sorted_movies = sort_movies_by_year(all_movies, descending=True)
    else:
        sorted_movies = sort_movies_by_rating(all_movies, descending=True)

    page = int(request.args.get('page', 1))
    total = len(sorted_movies)
    total_pages = max(1, math.ceil(total / MOVIES_PER_PAGE))
    page = max(1, min(page, total_pages))
    start = (page - 1) * MOVIES_PER_PAGE
    end = start + MOVIES_PER_PAGE
    movies = sorted_movies[start:end]

    for m in movies:
        if m[0] not in session['shown_ids']:
            session['shown_ids'].append(m[0])

    return render_template('home.html',
                           movies=movies,
                           user=user,
                           sort_by=sort_by,
                           page=page,
                           total_pages=total_pages,
                           movies_on_page=MOVIES_PER_PAGE)


@app.route('/rate_and_replace', methods=['POST'])
def rate_and_replace():
    user = session['user']
    data = request.get_json()
    mid = int(data['movie_id'])
    rating = data['rating']

    with sqlite3.connect('movies.db') as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO rated_movies_table (user_name, movie_id) VALUES (?,?)",
            (user, mid)
        )
        conn.commit()

    shown = session.get('shown_ids', [])
    if mid not in shown:
        shown.append(mid)
        session['shown_ids'] = shown

    return ('', 204)

@app.route('/filter', methods=['GET', 'POST'])
def filter_page():
    user = session.get('user')
    if not user:
        return redirect(url_for('index'))

    genres      = get_all_genres()
    countries   = get_all_countries()
    rated_ids   = get_rated_ids(user)

    results = None
    form    = request.form  

    if request.method == 'POST':
        global_search = bool(form.get('global_search'))

        year_from = form.get('year_from', type=int)
        year_to   = form.get('year_to',   type=int)

        sel_genres   = form.getlist('genres')
        sel_countries= form.getlist('countries')

        min_rating = form.get('min_rating', type=float)

        if global_search:
            pool = get_all_movies()
        else:
            pool = get_movies(session.get('genres', []),
                              exclude_ids=[],
                              limit=None)

        filtered = []
        for m in pool:
            mid, title, genre, year, desc, country, director, rating = m

            if year_from is not None and year < year_from:
                continue
            if year_to   is not None and year > year_to:
                continue

            if sel_genres:
                mg = [g.strip().lower() for g in genre.split(',')]
                if not any(s.lower() in mg for s in sel_genres):
                    continue

            if sel_countries and country not in sel_countries:
                continue

            if min_rating is not None and rating < min_rating:
                continue

            filtered.append(m)

        results = filtered

    return render_template('filter.html',
                           genres=genres,
                           countries=countries,
                           rated_ids=rated_ids,
                           results=results,
                           form=form)
    
if __name__ == '__main__':
    app.run(debug=True)
