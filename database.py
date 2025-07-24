import sqlite3

def init_db():
    conn = sqlite3.connect('movies.db')
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS movies_table (
        id          INTEGER PRIMARY KEY,
        title       TEXT,
        genre       TEXT,
        year        INTEGER,
        description TEXT,
        countries   TEXT,
        director    TEXT,
        rating      REAL
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS rated_movies_table (
        user_name  TEXT,
        movie_id   INTEGER,
        user_rating BOOLEAN,
        PRIMARY KEY (user_name, movie_id)
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS favorite_genres (
        user_name TEXT,
        genre     TEXT,
        PRIMARY KEY (user_name, genre)
    )""")

    conn.commit()
    conn.close()
