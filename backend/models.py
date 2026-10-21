from pydantic import BaseModel


class comment(BaseModel):
    id: int
    description: str
    likes: int | None = 0


class tweet(BaseModel):
    id: int
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
