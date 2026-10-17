#Мини-социальная сеть
#Пользователь, Публикации, Комментарии
from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from models import tweet,tweetCreate, tweetChange
from database import *
from sqlalchemy.sql import text



app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:3000","http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

#allTweets = []
#x = tweet(id = 0, title = "hello world", description = "first ever thing in the internet")
#y = tweet(id = 1, title = "hello world yet again", description="what there is not to love about python")
#z = tweet(id = 2, title = "goodbye world", description="all my homies HATE python")
#allTweets.append(x)
#allTweets.append(y)
#allTweets.append(z)

from fastapi.staticfiles import StaticFiles

@app.on_event("startup")
def seed_database():
    db = SessionLocal()
    try:
        # 1. Проверяем, есть ли уже твиты в базе. 
        # Это защитит от дубликатов при каждом перезапуске Docker-контейнера.
        if db.query(TweetDB).count() == 0:
            
            # 2. Создаем объекты для базы данных
            seed_tweets = [
                TweetDB(title="hello world", description="first ever thing in the internet", likes=0),
                TweetDB(title="hello world yet again", description="what there is not to love about python", likes=0),
                TweetDB(title="goodbye world", description="all my homies HATE python", likes=0)
            ]
            
            # 3. Сохраняем в БД
            db.add_all(seed_tweets)
            db.commit()
            print("✅ База данных успешно заполнена начальными твитами.")
        else:
            print("⏩ База данных уже содержит записи, пропускаем заполнение.")
    except Exception as e:
        print(f"❌ Ошибка при заполнении БД: {e}")
        db.rollback()
    finally:
        db.close()
@app.get("/tweet", response_model=list[tweet])
async def GetAllTweets(db=Depends(get_db)):
    allTweets = db.query(TweetDB).all()
    res = db.execute(text('select * from tweets'))
    for record in res.mappings().all():
        print("\n", tweet.validate(record))
    return allTweets

@app.delete("/tweet/{tweetId}", status_code=status.HTTP_204_NO_CONTENT)
async def deleteTweet(tweetId: int):
    try:
        allTweets.pop(tweetId)
    except IndexError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="tweet not found")

@app.get("/tweet/{tweetId}")
async def GetTweetById(tweetId: int):
    try:
        return allTweets[tweetId].model_dump(mode='json')
    except IndexError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="tweet not found")

@app.put("/tweet/{tweetId}")
async def changeTweet(tweetId: int, payload: tweetCreate):
    if tweetId < 0 or tweetId >= len(allTweets):
        raise HTTPException(status_code=404, detail="tweet not found")
    oldTweet = allTweets[tweetId]
    newTweet = tweet(
        id=tweetId,
        title=payload.title,
        description=payload.description,
        likes=oldTweet.likes,
    )
    allTweets[tweetId] = newTweet
    return newTweet.model_dump(mode='json')

@app.post("/tweet", status_code=status.HTTP_201_CREATED)
async def CreateTweet(payload: tweetCreate, db = Depends(get_db)):
    newTweet = TweetDB(title = payload.title, description = payload.description)
    db.add(newTweet)
    db.commit()
    