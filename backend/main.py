# Мини-социальная сеть
# Пользователь, Публикации, Комментарии
from typing import Annotated

import seed
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


# startup seeding of the db for testing
@app.on_event("startup")
async def onStart():
    seed.seed_database()


# user endpoints
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
    result = (
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
async def getMe(current_user: currentUser):
    return current_user


# tweet endpoints
@app.get("/tweet", response_model=list[tweet])
async def GetAllTweets(db=Depends(get_db)):
    res = db.execute(selectAllQuery)
    allTweets = map(tweet.model_validate, res.mappings().all())
    return allTweets


@app.delete("/tweet/{tweetId}", status_code=status.HTTP_200_OK)
async def deleteTweet(tweetId: int, current_user: currentUser, db=Depends(get_db)):
    try:
        res = tweet.model_validate(
            db.execute(selectOneQuery.bindparams(id=tweetId)).mappings().first()
        )
    except ValidationError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="tweet not found"
        )
    if res.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="not authorized to delete this post",
        )
    res = tweet.model_validate(
        db.execute(deleteOneQuery.bindparams(id=tweetId)).mappings().first()
    )
    db.commit()
    return res


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
async def changeTweet(
    tweetId: int, payload: tweetCreate, current_user: currentUser, db=Depends(get_db)
):
    try:
        res = tweet.model_validate(
            db.execute(selectOneQuery.bindparams(id=tweetId)).mappings().first()
        )
    except ValidationError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="tweet not found"
        )
    if res.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="not authorized to change this post",
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


@app.post("/tweet", status_code=status.HTTP_201_CREATED, response_model=tweet)
async def CreateTweet(
    payload: tweetCreate, current_user: currentUser, db=Depends(get_db)
):
    try:
        res = tweet.model_validate(
            db.execute(
                addOneQuery.bindparams(
                    title=payload.title,
                    description=payload.description,
                    owner_id=current_user.id,
                )
            )
            .mappings()
            .first()
        )
    except ValidationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="could not create post"
        )
    db.commit()
    return res


# comment endpoints
@app.post(
    "/tweet/{tweetId}/comments",
    response_model=comment,
    status_code=status.HTTP_201_CREATED,
)
async def createComment(
    tweetId: int,
    payload: commentCreate,
    current_user: currentUser,
    db=Depends(get_db),
):
    try:
        tweet.model_validate(
            db.execute(selectOneQuery.bindparams(id=tweetId)).mappings().first()
        )
    except ValidationError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="tweet not found"
        )
    try:
        res = comment.model_validate(
            db.execute(
                addOneCommentQuery.bindparams(
                    description=payload.description,
                    post=tweetId,
                    owner_id=current_user.id,
                )
            )
            .mappings()
            .first()
        )
    except ValidationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="could not create tweet"
        )
    db.commit()
    return res


@app.delete("/comments/{commentId}", status_code=status.HTTP_200_OK)
async def deleteComment(commentId: int, current_user: currentUser, db=Depends(get_db)):
    try:
        res = comment.model_validate(
            db.execute(selectOneCommentQuery.bindparams(id=commentId))
            .mappings()
            .first()
        )
    except ValidationError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="comment not found"
        )
    if res.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="not authorized to delete this comment",
        )

    res = comment.model_validate(
        db.execute(deleteOneCommentQuery.bindparams(id=commentId)).mappings().first()
    )
    db.commit()
    return res


@app.put("/comments/{commentId}", status_code=status.HTTP_200_OK)
async def changeComment(
    commentId: int,
    current_user: currentUser,
    payload: commentCreate,
    db=Depends(get_db),
):
    try:
        res = comment.model_validate(
            db.execute(selectOneCommentQuery.bindparams(id=commentId))
            .mappings()
            .first()
        )
    except ValidationError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="comment not found"
        )
    if res.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="not authorized to delete this comment",
        )
    res = comment.model_validate(
        db.execute(
            changeOneCommentQuery.bindparams(
                id=commentId, description=payload.description
            )
        )
        .mappings()
        .first()
    )
    db.commit()
    return res
