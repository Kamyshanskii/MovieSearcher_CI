def test_get_all_genres(app):
    with app.app_context():
        from app import get_all_genres
        genres = get_all_genres()
        assert isinstance(genres, list)
        assert len(genres) > 0
        assert all(isinstance(g, str) for g in genres)

def test_get_all_countries(app):
    with app.app_context():
        from app import get_all_countries
        countries = get_all_countries()
        assert isinstance(countries, list)
        assert len(countries) > 0
        assert all(isinstance(c, str) for c in countries)

def test_get_movies(app, auth_client):
    with app.app_context():
        from app import get_movies
        with auth_client:
            movies = get_movies(['drama'])
            assert isinstance(movies, list)
            if movies:
                assert len(movies[0]) == 8  # Проверка структуры данных фильма

def test_get_rated_ids(app, test_user):
    with app.app_context():
        from app import get_rated_ids
        rated_ids = get_rated_ids(test_user)
        assert isinstance(rated_ids, list)
        assert all(isinstance(i, int) for i in rated_ids)

def test_are_similar_users(app, test_user):
    with app.app_context():
        from app import are_similar_users
        # Добавляем тестовые данные в БД
        conn = app.config['DATABASE']
        conn.execute("""
        INSERT INTO rated_movies_table VALUES 
            ('user1', 1, 1),
            ('user1', 2, 1),
            ('user2', 1, 1),
            ('user2', 2, 0)
        """)
        
        result = are_similar_users('user1', 'user2')
        assert isinstance(result, bool)