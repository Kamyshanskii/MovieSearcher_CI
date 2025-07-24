import sqlite3
import csv
from database import init_db
import os

def import_kinopoisk_top250(csv_path='kinopoisk-top250.csv', db_path='movies.db'):
    init_db()

    csv_path = os.path.abspath(csv_path)
    db_path  = os.path.abspath(db_path)

    conn = sqlite3.connect(db_path)
    cur  = conn.cursor()

    with open(csv_path, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader, start=1):
            movie_id = idx
            title = row.get('movie', '').strip()
            genre = row.get('genres', '').strip().strip('"')
            year_txt = row.get('year', '').strip()
            try:
                year = int(year_txt)
            except ValueError:
                year = None
            description = row.get('overview', '').strip()
            countries = row.get('country', '').strip()
            director = row.get('director', '').strip()
            rating_txt = row.get('rating_ball', '').replace(',', '.').strip()
            try:
                rating = float(rating_txt)
            except ValueError:
                rating = None

            cur.execute("""
                INSERT OR REPLACE INTO movies_table
                  (id, title, genre, year, description, countries, director, rating)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                movie_id,
                title,
                genre,
                year,
                description,
                countries,
                director,
                rating
            ))

    conn.commit()
    conn.close()
    print(f"Импорт Завершен")

if __name__ == "__main__":
    import_kinopoisk_top250()
