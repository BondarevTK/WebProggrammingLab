import pytest
from fastapi.testclient import TestClient

import main
from main import app, allTweets


@pytest.fixture
def client():
    """Клиент FastAPI. Сбрасывает состояние перед каждым тестом."""
    original = list(allTweets)
    yield TestClient(app)
    allTweets.clear()
    allTweets.extend(original)

def test_get_all_tweets_returns_list(client):
    """Успешный сценарий: список возвращается, статус 200."""
    response = client.get("/tweet")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 3


    first = data[0]
    assert "id" in first
    assert "title" in first
    assert "description" in first
    assert "likes" in first

def test_get_tweet_by_id_success(client):
    """Успешный сценарий: получаем твит с существующим id."""
    response = client.get("/tweet/1")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == 1
    assert data["title"] == "hello world yet again"


def test_get_tweet_by_id_not_found(client):
    """Ошибочный сценарий: id вне диапазона → 400."""
    response = client.get("/tweet/999")
    assert response.status_code == 400
    assert "detail" in response.json()

def test_create_tweet_success(client):
    """Успешный сценарий: создаём твит, получаем 201 и id."""
    payload = {"title": "Новый пост", "description": "Тело поста"}
    response = client.post("/tweet", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Новый пост"
    assert data["description"] == "Тело поста"
    assert data["id"] == 3          # idCounter после трёх стартовых

    # Проверяем, что твит реально добавился
    list_response = client.get("/tweet")
    assert len(list_response.json()) == 4


def test_create_tweet_invalid_payload(client):
    """Ошибочный сценарий: не хватает поля → 422."""
    payload = {"title": "Только заголовок"}    # нет description
    response = client.post("/tweet", json=payload)

    assert response.status_code == 422
    assert "detail" in response.json()

def test_update_tweet_success(client):
    """Успешный сценарий: меняем title и description."""
    payload = {"title": "Изменён", "description": "Новое тело"}
    response = client.put("/tweet/0", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Изменён"
    assert data["description"] == "Новое тело"
    assert data["id"] == 0


def test_update_tweet_not_found(client):
    """Ошибочный сценарий: обновляем несуществующий id → 400."""
    payload = {"title": "X", "description": "Y"}
    response = client.put("/tweet/999", json=payload)

    assert response.status_code == 404
    assert "detail" in response.json()


def test_update_tweet_invalid_payload(client):
    """Ошибочный сценарий: пустое тело → 422."""
    response = client.put("/tweet/0", json={})
    assert response.status_code == 422

def test_delete_tweet_success(client):
    """Успешный сценарий: удаляем твит, список уменьшается."""
    before = len(client.get("/tweet").json())
    response = client.delete("/tweet/0")
    assert response.status_code == 204

    after = len(client.get("/tweet").json())
    assert after == before - 1


def test_delete_tweet_not_found(client):
    """Ошибочный сценарий: удаляем несуществующий id → 400."""
    response = client.delete("/tweet/999")
    assert response.status_code == 400
    assert "detail" in response.json()

def test_state_isolation(client):
    """После предыдущих тестов состояние должно быть исходным."""
    data = client.get("/tweet").json()
    assert len(data) == 3
    assert data[0]["title"] == "hello world"