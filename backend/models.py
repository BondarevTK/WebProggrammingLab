from pydantic import BaseModel, ConfigDict

class tweet(BaseModel):
    id: int
    title: str
    description: str
    likes: int | None = 0
    imageUrl: str | None="/images/default.jpg"

    model_config = ConfigDict(from_attributes=True)

class tweetCreate(BaseModel):
    title: str
    description: str

class tweetChange(BaseModel):
    id: int
    title: str
    description: str