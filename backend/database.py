import os
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.sql import text

databaseUrl = os.environ["DATABASE_URL"]
engine = create_engine(databaseUrl)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class TweetDB(Base):
    __tablename__ = "tweets"
    id = Column(Integer, primary_key=True)
    title = Column(String, index=True)
    description = Column(String)
    likes = Column(Integer, default=0)
    created = Column(DateTime, default=datetime.now())


class commentDB(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True)
    post = Column(Integer, ForeignKey("tweets.id", ondelete="CASCADE"), nullable=False)
    description = Column(String)
    likes = Column(Integer, default=0)
    created = Column(DateTime, default=datetime.now())


Base.metadata.create_all(bind=engine)


selectAllQuery = text(
    "select id, title, description, likes from tweets ORDER BY id DESC"
)
# needs {"tweetId":tweetId}
selectOneQuery = text("select id, title, description, likes from tweets where id=:id")
addOneQuery = text("insert into tweets(title,description) values(:title,:description)")
addOneCommentQuery = text(
    "insert into comments(post,description) values(:post,:description)"
)
changeOneQuery = text(
    "update tweets set title=:title,description=:description where id=:id"
)
deleteOneQuery = text("delete from tweets where id=:id")
deleteOneCommentQuery = text("delete from comments where id=:id")


selectOneWithCommentsQuery = text("""SELECT t.id, t.title, t.description, t.likes,
                COALESCE(json_agg(json_build_object('id', c.id, 'description', c.description, 'likes', c.likes)) FILTER (WHERE c.id IS NOT NULL), '[]')
                AS comments
                FROM tweets t
                LEFT JOIN comments c ON t.id = c.post
                WHERE t.id = :id
                GROUP BY t.id
                """)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
