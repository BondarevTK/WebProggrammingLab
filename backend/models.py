from pydantic import BaseModel, EmailStr
from pydantic.fields import Field


class comment(BaseModel):
    id: int
    owner_id: int
    owner_username: str
    description: str
    likes: int | None = 0


class tweet(BaseModel):
    id: int
    owner_id: int
    username: str
    title: str
    description: str
    comments: list[comment] | None = []
    likes: int | None = 0
    imageUrl: str | None = "/images/default.jpg"


class tweetCreate(BaseModel):
    title: str
    description: str


class commentCreate(BaseModel):
    description: str


class User(BaseModel):
    id: int
    username: str = Field(min_length=4)
    email: EmailStr
    passhash: str


class UserCreate(BaseModel):
    username: str = Field(min_length=4)
    email: EmailStr
    passwordUnhashed: str = Field(min_length=4)


class Token(BaseModel):
    access_token: str
    token_type: str
