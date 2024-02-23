import datetime
from sqlalchemy import Column, Integer, String, TIMESTAMP
from datetime import datetime

from .database import Base


class audioFile(Base):
    __tablename__ = "audioFiles"

    id = Column(Integer, primary_key=True, index=True)
    timeStamp = Column(TIMESTAMP, default=datetime.utcnow)  #yr,month,day,hr,min,second
    uri = Column(String, unique=True)   #url to image
    location = Column(Integer)  #which sound thing



class storyFile(Base):
    __tablename__ = "storyFiles"
    
    id = Column(Integer, primary_key=True, index=True)
    count = Column(Integer)
    imageUri = Column(String, unique=True)   #url to image
    textUri = Column(String, nullable=True, unique=True)
    category = Column(String)
