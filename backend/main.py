# Мини-социальная сеть
# Пользователь, Публикации, Комментарии
from database import *
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from models import commentCreate, tweet, tweetCreate
from pydantic import ValidationError

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:3000", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# allTweets = []
# x = tweet(id = 0, title = "hello world", description = "first ever thing in the internet")
# y = tweet(id = 1, title = "hello world yet again", description="what there is not to love about python")
# z = tweet(id = 2, title = "goodbye world", description="all my homies HATE python")
# allTweets.append(x)
# allTweets.append(y)
# allTweets.append(z)


@app.on_event("startup")
def seed_database():
    db = SessionLocal()
    try:
        # 1. Проверяем, есть ли уже твиты в базе.
        # Это защитит от дубликатов при каждом перезапуске Docker-контейнера.
        seed_tweets = [
            TweetDB(
                title="hello world",
                description="first ever thing in the internet",
                likes=0,
            ),
            TweetDB(
                title="hello world yet again",
                description="what there is not to love about python",
                likes=0,
            ),
            TweetDB(
                title="goodbye world",
                description="all my homies HATE python",
                likes=0,
            ),
            commentDB(description="so true oomfie", post=1, likes=0),
        ]

        # 3. Сохраняем в БД
        db.add_all(seed_tweets)
        db.commit()
        print("✅ База данных успешно заполнена начальными твитами.")
    except Exception as e:
        print(f"❌ Ошибка при заполнении БД: {e}")
        db.rollback()
    finally:
        db.close()


@app.get("/tweet", response_model=list[tweet])
async def GetAllTweets(db=Depends(get_db)):
    res = db.execute(selectAllQuery)
    allTweets = map(tweet.model_validate, res.mappings().all())
    return allTweets


@app.delete("/tweet/{tweetId}", status_code=status.HTTP_204_NO_CONTENT)
async def deleteTweet(tweetId: int, db=Depends(get_db)):
    try:
        db.execute(deleteOneQuery.bindparams(id=tweetId))
        db.commit()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="tweet not found"
        )


@app.get("/tweet/{tweetId}")
async def GetTweetById(tweetId: int, db=Depends(get_db)):
    try:
        res = tweet.model_validate(
            db.execute(selectOneWithCommentsQuery.bindparams(id=tweetId))
            .mappings()
            .first()
        )
        return res
    except ValidationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="tweet not found"
        )


@app.put("/tweet/{tweetId}")
async def changeTweet(tweetId: int, payload: tweetCreate, db=Depends(get_db)):
    try:
        tweet.model_validate(
            db.execute(selectOneQuery.bindparams(id=tweetId)).mappings().first()
        )
        db.execute(
            changeOneQuery.bindparams(
                id=tweetId, title=payload.title, description=payload.description
            )
        )
        db.commit()
        return tweet.model_validate(
            db.execute(selectOneQuery.bindparams(id=tweetId)).mappings().first()
        )
    except ValidationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="something went wrong"
        )


@app.post("/tweet", status_code=status.HTTP_201_CREATED)
async def CreateTweet(payload: tweetCreate, db=Depends(get_db)):
    db.execute(
        addOneQuery.bindparams(title=payload.title, description=payload.description)
    )
    db.commit()


@app.post("/tweet/{tweetId}/comments")
async def createComment(tweetId: int, payload: commentCreate, db=Depends(get_db)):
    db.execute(
        addOneCommentQuery.bindparams(description=payload.description, post=tweetId)
    )
    db.commit()


@app.delete("/comments/{commentId}", status_code=status.HTTP_200_OK)
async def deleteComment(commentId: int, db=Depends(get_db)):
    try:
        db.execute(deleteOneCommentQuery.bindparams(id=commentId))
        db.commit()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="tweet not found"
        )
