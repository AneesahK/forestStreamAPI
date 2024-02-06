import datetime
from sqlalchemy import Column, Integer, String, TIMESTAMP
from datetime import datetime

from .database import Base
# from database import Base


class audioFile(Base):
    __tablename__ = "audioFiles"

    id = Column(Integer, primary_key=True, index=True)
    timeStamp = Column(TIMESTAMP, default=datetime.utcnow)  #yr,month,day,hr,min,second
    # date = Column(TIMESTAMP)
    # order = Column(Integer) #first in timestamp, or second etc
    uri = Column(String, unique=True)   #url to image
    location = Column(Integer)  #which sound thing
