from sqlalchemy import create_engine, Column, Integer, String, Identity
from sqlalchemy.orm import declarative_base, sessionmaker
import os

databaseUrl = os.getenv("DATABASE_URL")
if databaseUrl:
    engine = create_engine(databaseUrl)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()



class TweetDB(Base):
    __tablename__ = "tweets"
    id = Column(Integer, primary_key=True)
    title = Column(String, index=True)
    description = Column(String)
    likes = Column(Integer, default=0)
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()