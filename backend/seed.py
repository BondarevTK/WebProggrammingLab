from auth import *
from database import *


def seed_database():
    db = SessionLocal()

    # Проверяем, есть ли уже данные. Если есть — не заполняем.
    if db.query(UserDB).count() > 0:
        print("⏩ База данных уже заполнена. Пропускаем сидирование.")
        db.close()
        return

    try:
        # 1. Создаем 10 пользователей
        users = []
        for i in range(1, 11):
            user = UserDB(
                username=f"user_{i}",
                email=f"user{i}@example.com",
                passhash=hash_password(f"password{i}"),
            )
            users.append(user)
            db.add(user)

        # Коммитим, чтобы у пользователей появились ID (от 1 до 10)
        db.commit()

        # 2. Создаем 10 постов (распределяем их между пользователями)
        tweets = []
        for i in range(1, 11):
            # Берем владельца из списка (i-1, так как индексы начинаются с 0)
            owner = users[i - 1]
            tweet = TweetDB(
                title=f"Post number {i}",
                description=f"This is the great content of post #{i}. Written by {owner.username}.",
                likes=i * 3,  # Просто для разнообразия
                owner_id=owner.id,
            )
            tweets.append(tweet)
            db.add(tweet)

        # Коммитим, чтобы у постов появились ID
        db.commit()

        # 3. Создаем 10 комментариев (к разным постам от разных юзеров)
        for i in range(1, 11):
            # Комментарий пишет не тот, кто создал пост (чтобы было интереснее)
            commenter = users[(i + 4) % 10]
            # Комментируем разные посты
            target_tweet = tweets[i % 10]

            comment = commentDB(
                description=f"Wow, post #{i} is awesome! Sincerely, {commenter.username}.",
                post=target_tweet.id,
                likes=i,
                owner_id=commenter.id,
            )
            db.add(comment)

        db.commit()
        print(
            "✅ База данных успешно заполнена: 10 юзеров, 10 постов, 10 комментариев."
        )

    except Exception as e:
        print(f"❌ Ошибка при заполнении БД: {e}")
        db.rollback()
    finally:
        db.close()
