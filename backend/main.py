# Мини-социальная сеть
# Пользователь, Публикации, Комментарии
from typing import Annotated

from auth import *
from database import *
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from models import Token, User, UserCreate, comment, commentCreate, tweet, tweetCreate
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


@app.post("/user", response_model=User)
async def createUser(payload: UserCreate, db=Depends(get_db)):
    res = (
        db.execute(
            text(
                "select username,email from users where username=:username"
            ).bindparams(username=payload.username)
        )
        .mappings()
        .first()
    )
    if res:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="username already exists"
        )
    res = (
        db.execute(
            text("select * from users where email=:email").bindparams(
                email=payload.email.lower()
            )
        )
        .mappings()
        .first()
    )
    if res:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="email is already registered",
        )
    new_user = User.model_validate(
        db.execute(
            text(
                "insert into users(username,email,passhash) values(:username,:email,:passhash) returning id,username,email,passhash"
            ).bindparams(
                username=payload.username,
                email=payload.email.lower(),
                passhash=hash_password(payload.passwordUnhashed),
            )
        )
        .mappings()
        .first()
    )
    db.commit()
    return new_user


@app.post("/token", response_model=Token)
async def loginToken(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db=Depends(get_db)
):
    result = User.model_validate(
        db.execute(
            text("select * from users where email = :email").bindparams(
                email=form_data.username.lower()
            )
        )
        .mappings()
        .first()
    )
    if not result or not verify_password(form_data.password, result.passhash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="incorrect password or email",
            headers={"WWW-Authenticate": "Bearer"},
        )
    accToken = create_access_token(data={"sub": str(result.id)})
    return Token(access_token=accToken, token_type="bearer")


@app.get("/me", response_model=User)
async def get_current_user(token=Depends(oauth2_scheme), db=Depends(get_db)):
    """Get the currently authenticated user."""
    user_id = verify_access_token(token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Validate user_id is a valid integer (defense against malformed JWT)
    try:
        user_id_int = int(user_id)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = (
        db.execute(
            text("select * from users where id = :id").bindparams(id=user_id_int)
        )
        .mappings()
        .first()
    )
    user = User.model_validate(result)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


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


@app.get("/tweet/{tweetId}", response_model=tweet)
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
            status_code=status.HTTP_404_NOT_FOUND, detail="tweet not found"
        )


@app.put("/tweet/{tweetId}", response_model=tweet)
async def changeTweet(tweetId: int, payload: tweetCreate, db=Depends(get_db)):
    try:
        tweet.model_validate(
            db.execute(selectOneQuery.bindparams(id=tweetId)).mappings().first()
        )
        res = (
            db.execute(
                changeOneQuery.bindparams(
                    id=tweetId, title=payload.title, description=payload.description
                )
            )
            .mappings()
            .first()
        )
        db.commit()
        return res
    except ValidationError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="tweet not found"
        )


@app.post("/tweet", status_code=status.HTTP_201_CREATED, response_model=tweet)
async def CreateTweet(payload: tweetCreate, db=Depends(get_db)):
    res = tweet.model_validate(
        db.execute(
            addOneQuery.bindparams(title=payload.title, description=payload.description)
        )
        .mappings()
        .first()
    )
    db.commit()
    return res


@app.post(
    "/tweet/{tweetId}/comments",
    response_model=comment,
    status_code=status.HTTP_201_CREATED,
)
async def createComment(tweetId: int, payload: commentCreate, db=Depends(get_db)):
    thisTweet = tweet.model_validate(
        db.execute(selectOneQuery.bindparams(id=tweetId)).mappings().first()
    )
    if not thisTweet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="tweet not found"
        )
    else:
        res = comment.model_validate(
            db.execute(
                addOneCommentQuery.bindparams(
                    description=payload.description, post=tweetId
                )
            )
            .mappings()
            .first()
        )
        db.commit()
        return res


@app.delete("/comments/{commentId}", status_code=status.HTTP_200_OK)
async def deleteComment(commentId: int, db=Depends(get_db)):
    try:
        db.execute(deleteOneCommentQuery.bindparams(id=commentId))
        db.commit()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="something went wrong"
        )
