from pydantic import BaseModel

class tweet(BaseModel):
    id: int
    title: str
    description: str
    likes: int | None = 0
    imageUrl: str | None="/images/default.jpg"

class tweetCreate(BaseModel):
    title: str
    description: str

class tweetChange(BaseModel):
    id: int
    title: str
    description: str