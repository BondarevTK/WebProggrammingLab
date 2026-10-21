import pytest
from database import SessionLocal, TweetDB, commentDB
from fastapi.testclient import TestClient
from main import app

# Создаем тестовый клиент
client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_database():
    """
    Фикстура запускается ПЕРЕД каждым тестом.
    Она очищает таблицы в базе данных, чтобы тесты не влияли друг на друга.
    """
    db = SessionLocal()
    try:
        # Удаляем сначала комментарии (из-за Foreign Key), затем твиты
        db.query(commentDB).delete()
        db.query(TweetDB).delete()
        db.commit()

        # Добавляем базовый твит для тестов (id=1)
        test_tweet = TweetDB(id=1, title="Test", description="Test desc", likes=0)
        db.add(test_tweet)
        db.commit()
    finally:
        db.close()

    yield  # Здесь выполняется сам тест

    # После теста можно тоже почистить, но для простоты достаточно очистки в начале


# ==========================================
# Тесты для твитов (GET, POST, PUT, DELETE)
# ==========================================


def test_get_all_tweets():
    """Успешный сценарий: получение списка твитов."""
    response = client.get("/tweet")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["title"] == "Test"


def test_create_tweet():
    """Успешный сценарий: создание нового твита."""
    payload = {"title": "New tweet", "description": "New description"}
    response = client.post("/tweet", json=payload)
    assert response.status_code == 201

    # Проверяем, что твит добавился
    get_response = client.get("/tweet")
    assert len(get_response.json()) == 2


def test_get_tweet_by_id():
    """Успешный сценарий: получение одного твита по ID."""
    response = client.get("/tweet/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["title"] == "Test"


def test_get_tweet_not_found():
    """Ошибочный сценарий: запрос несуществующего твита."""
    # В вашем коде ловится ValidationError и возвращается 400
    response = client.get("/tweet/999")
    assert response.status_code == 400
    assert response.json()["detail"] == "tweet not found"


def test_update_tweet():
    """Успешный сценарий: обновление твита."""
    payload = {"title": "Updated", "description": "Updated desc"}
    response = client.put("/tweet/1", json=payload)
    assert response.status_code == 200

    # Проверяем, что данные изменились
    get_response = client.get("/tweet/1")
    assert get_response.json()["title"] == "Updated"


def test_delete_tweet():
    """Успешный сценарий: удаление твита."""
    response = client.delete("/tweet/1")
    assert response.status_code == 204

    # Проверяем, что твит удален
    get_response = client.get("/tweet/1")
    assert get_response.status_code == 400


# ==========================================
# Тесты для комментариев
# ==========================================


def test_create_comment():
    """Успешный сценарий: добавление комментария к твиту."""
    payload = {"description": "Nice post!"}
    response = client.post("/tweet/1/comments", json=payload)
    assert response.status_code == 200  # У вас не указан status_code=201, поэтому 200

    # Проверяем через GET /tweet/1, что комментарий подтянулся (благодаря JSON_AGG)
    get_response = client.get("/tweet/1")
    assert get_response.status_code == 200
    data = get_response.json()

    assert len(data["comments"]) == 1
    assert data["comments"][0]["description"] == "Nice post!"


def test_delete_comment():
    """Успешный сценарий: удаление комментария."""
    # 1. Создаем комментарий
    client.post("/tweet/1/comments", json={"description": "To be deleted"})

    # 2. Получаем его ID
    get_response = client.get("/tweet/1")
    comment_id = get_response.json()["comments"][0]["id"]

    # 3. Удаляем
    response = client.delete(f"/comments/{comment_id}")
    assert response.status_code == 200

    # 4. Проверяем, что он исчез
    get_response = client.get("/tweet/1")
    assert len(get_response.json()["comments"]) == 0
