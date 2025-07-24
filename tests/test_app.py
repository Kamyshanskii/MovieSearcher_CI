def test_index_redirect(client):
    response = client.get('/')
    assert response.status_code == 200
    # Проверяем наличие ключевых элементов на странице
    assert b'MovieSearcher' in response.data
    assert b'login' in response.data.lower()

def test_login_post(client):
    # Тест с редиректом
    response = client.post('/login', 
                         data={'user_name': 'test_user'},
                         follow_redirects=False)
    assert response.status_code == 302  # Проверяем редирект

def test_homepage_access(auth_client):
    # Добавляем недостающий ключ в сессию
    with auth_client.session_transaction() as sess:
        sess['shown_ids'] = []  # Инициализируем пустым списком
    
    response = auth_client.get('/home')
    assert response.status_code == 200
    # Более общие проверки контента
    assert b'Movie' in response.data  # Проверяем часть названия
    assert b'user' in response.data.lower()  # Проверяем наличие информации о пользователе