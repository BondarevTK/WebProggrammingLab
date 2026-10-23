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
    owner_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title = Column(String, index=True)
    description = Column(String)
    likes = Column(Integer, default=0)
    created = Column(DateTime, default=datetime.now())


class commentDB(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True)
    owner_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    post = Column(Integer, ForeignKey("tweets.id", ondelete="CASCADE"), nullable=False)
    description = Column(String)
    likes = Column(Integer, default=0)
    created = Column(DateTime, default=datetime.now())


class UserDB(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    passhash = Column(String, nullable=False)


Base.metadata.create_all(bind=engine)

# Tweet queries
selectAllQuery = text(
    "SELECT t.id, t.title, t.description, t.likes, t.owner_id, u.username from tweets t left join users u on t.owner_id = u.id ORDER BY id DESC"
)
selectOneQuery = text(
    "SELECT t.id, t.title, t.description, t.likes, t.owner_id, u.username from tweets t left join users u on t.owner_id = u.id where t.id=:id"
)
addOneQuery = text(
    "INSERT into tweets(title,description,likes, owner_id) values(:title,:description,0,:owner_id) RETURNING id, owner_id,title, description, likes"
)
changeOneQuery = text(
    "UPDATE tweets set title=:title,description=:description where id=:id RETURNING id, title, description, likes, owner_id"
)
deleteOneQuery = text(
    "DELETE from tweets where id=:id RETURNING id, title, description, likes, owner_id"
)


# Comment queries
deleteOneCommentQuery = text(
    "DELETE from comments where id=:id returning id,owner_id,description,likes"
)
addOneCommentQuery = text(
    "INSERT into comments(post,description,likes, owner_id) values(:post,:description,0,:owner_id) RETURNING id, description, likes, owner_id"
)
changeOneCommentQuery = text(
    "UPDATE comments set description=:description where id=:id RETURNING id, description, likes, owner_id"
)
selectOneCommentQuery = text(
    "SELECT id, owner_id, description, likes from comments where id=:id"
)

selectOneWithCommentsQuery = text("""SELECT t.id, t.title, t.description, t.likes, t.owner_id, u.username,
                COALESCE(json_agg(json_build_object('id', c.id, 'description', c.description, 'likes', c.likes, 'owner_id', c.owner_id,'owner_username', cu.username)) FILTER (WHERE c.id IS NOT NULL), '[]')
                AS comments
                FROM tweets t
                LEFT JOIN users u ON t.owner_id = u.id
                LEFT JOIN comments c ON t.id = c.post
                LEFT JOIN users cu ON c.owner_id = cu.id
                WHERE t.id = :id
                GROUP BY t.id, u.username
                """)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
