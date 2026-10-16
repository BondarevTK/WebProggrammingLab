#Мини-социальная сеть
#Пользователь, Публикации, Комментарии
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from models import tweet,tweetCreate, tweetChange



app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

allTweets = []
x = tweet(id = 0, title = "hello world", description = "first ever thing in the internet")
y = tweet(id = 1, title = "hello world yet again", description="what there is not to love about python")
z = tweet(id = 2, title = "goodbye world", description="all my homies HATE python")
allTweets.append(x)
allTweets.append(y)
allTweets.append(z)

from fastapi.staticfiles import StaticFiles

@app.get("/tweet")
async def GetAllTweets():
    alltweetsJson = []
    for i in allTweets:
        item = i.model_dump(mode="json")
        alltweetsJson.append(item)
    return alltweetsJson

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

idCounter = 3
@app.post("/tweet", response_model=tweet, status_code=status.HTTP_201_CREATED)
async def CreateTweet(payload: tweetCreate):
    global idCounter
    newTweet = tweet(id= idCounter, title = payload.title, description = payload.description)
    allTweets.append(newTweet)
    idCounter+=1
    return newTweet.model_dump(mode='json')
    