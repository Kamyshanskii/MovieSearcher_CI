import pytest
from app import app as flask_app
import sqlite3

@pytest.fixture
def app():
    flask_app.config['TESTING'] = True
    flask_app.config['SECRET_KEY'] = 'test-secret-key'
    flask_app.config['WTF_CSRF_ENABLED'] = False
    
    with flask_app.app_context():
        conn = sqlite3.connect(':memory:')
        cur = conn.cursor()
        
        cur.executescript("""
        CREATE TABLE movies_table (
            id INTEGER PRIMARY KEY,
            title TEXT,
            genre TEXT,
            year INTEGER,
            description TEXT,
            countries TEXT,
            director TEXT,
            rating REAL
        );
        
        INSERT INTO movies_table VALUES 
            (1, 'Test Movie', 'drama, crime', 1994, 'Description', 'USA', 'Director', 9.1);
        
        CREATE TABLE rated_movies_table (
            user_name TEXT,
            movie_id INTEGER,
            user_rating BOOLEAN,
            PRIMARY KEY (user_name, movie_id)
        );
        
        CREATE TABLE favorite_genres (
            user_name TEXT,
            genre TEXT,
            PRIMARY KEY (user_name, genre)
        );
        
        INSERT INTO favorite_genres VALUES ('test_user', 'drama');
        """)
        
        flask_app.config['DATABASE'] = conn
    yield flask_app
    
    with flask_app.app_context():
        conn.close()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_client(client):
    with client.session_transaction() as sess:
        sess['user'] = 'test_user'
        sess['genres'] = ['drama']
        sess['shown_ids'] = []
    return client

@pytest.fixture
def test_user():
    return 'test_user'