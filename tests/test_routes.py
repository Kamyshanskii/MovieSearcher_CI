import pytest
from flask import session, url_for

def test_index_redirect(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'MovieSearcher' in response.data
    assert b'login' in response.data.lower()

def test_home_page(auth_client):
    response = auth_client.get('/home')
    assert response.status_code == 200
    assert b'sort_by' in response.data

def test_filter_page(auth_client):
    response = auth_client.get('/filter')
    assert response.status_code == 200
    assert b'filter' in response.data.lower()

def test_rate_movies_page(auth_client):
    response = auth_client.get('/rate_movies')
    assert response.status_code == 200
    assert b'rate' in response.data.lower()