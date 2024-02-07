from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from fastapi.responses import FileResponse

from contextlib import asynccontextmanager
import os
import datetime
import json

from .database import SessionLocal, engine
from . import models

# Use migrations normally
app = FastAPI()

app_audio = FastAPI()

models.Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        

async def initialize_dbAudio(app: FastAPI):
    db = SessionLocal()
    num_sound = db.query(models.audioFile).count()

    current_path = os.getcwd()
    target_path = os.path.join("static", "tenSecChunks")
    os.chdir(target_path)
    songs = os.listdir()

    if num_sound != len(songs):
        # doesn't consider deletion of tracks and then addiiton, so will treat as number
        # if you do, delete whole table
        for sound in songs:
            stringS = sound.replace(".WAV", "").split("_")
            offsetTime = int(stringS[2]) - 10
            timeStampS = datetime.datetime(int(stringS[0][:4]), int(stringS[0][4:6]), int(stringS[0][6:]), int(stringS[1][:2]), int(stringS[1][2:4]), int(stringS[1][4:]))
            timeStampS = timeStampS + datetime.timedelta(seconds=offsetTime)
            locationS = stringS[3]

            if db.query(models.audioFile).filter_by(uri="/audio/{}".format(sound)).count() == 0:
                completeJ = {"timeStamp": timeStampS, "uri": "/audio/{}".format(sound), "location": locationS}
                db.add(models.audioFile(**completeJ))
                db.commit()

    db.close()
    os.chdir(current_path)

async def initialize_dbStory(app: FastAPI):
    db = SessionLocal()
    num_sound = db.query(models.storyFile).count()

    with open('category.json') as f:
        d = json.load(f)
    print(len(d))


    current_path = os.getcwd()
    target_path = os.path.join("static", "stories")
    os.chdir(target_path)
    sto = os.listdir()

    if num_sound != len(sto):
        for p in sto:
            stringS = p.split(".")[0]           ##names with no dots
            c = d[stringS.split("_")[-1]]

            if db.query(models.storyFile).filter_by(uri="/story/{}".format(p)).count() == 0:
                completeJ = {"uri":"/story/{}".format(p), "count":int(stringS.split("_")[-2]), "category":c}
                db.add(models.storyFile(**completeJ))
                db.commit()

    db.close()
    os.chdir(current_path)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await initialize_dbAudio(app)
    await initialize_dbStory(app)
    yield

app = FastAPI(lifespan=lifespan)

app.mount("/audio", StaticFiles(directory=("static/tenSecChunks")), name="audio")
app.mount("/story", StaticFiles(directory=("static/stories")), name="story")

@app.get("/getAudioFiles")
def getAudioFiles(
    startTime: int,     # 110207 -> 11.02 am 7 seconds
    duration: int,      # 60 -> 60 mins = 1hr
    locationG: int,      # 2 -> location number
    db: Session = Depends(get_db)   #access to db session
):
    start = datetime.datetime.now()
    start = start.replace(hour=int(str(startTime)[0:2]), minute=int(str(startTime)[2:4]), second=int(str(startTime)[4:]), microsecond=0)
    end = start + datetime.timedelta(minutes=duration)  #adding minutes
    endString = end.strftime('%Y-%m-%d %H%M%S')
    endString = endString.split(" ")[1]

    query = db.query(
        models.audioFile.uri
        ).filter(
            func.extract('hour', models.audioFile.timeStamp) * 3600 +
            func.extract('minute', models.audioFile.timeStamp) * 60 +
            func.extract('second', models.audioFile.timeStamp) >= int(str(startTime)[0:2]) *3600 + int(str(startTime)[2:4]) * 60  + int(str(startTime)[4:]), 
            func.extract('hour', models.audioFile.timeStamp) * 3600 +
            func.extract('minute', models.audioFile.timeStamp) * 60 +
            func.extract('second', models.audioFile.timeStamp) <= int(str(endString)[0:2]) *3600 + int(str(endString)[2:4]) * 60  + int(str(endString)[4:]),
            models.audioFile.location == locationG
            ).all()
    
    print(query)
    for q in query:
        print(q[0])

    # result = [{"uri":q[0]} for q in query]
    result = [q[0] for q in query]

    return result       #list of dict, NOW LIST

@app.get("/getAllStory")    #gives whole branch
def home(
    cate: int,          #category of the 4 in json
    prizeCount: int,     #Counter for the prize count they are on
    db: Session = Depends(get_db)   #access to db session
):
    with open('category.json') as f:
        d = json.load(f)
        categoryWord = d[str(cate)]
    
    query = db.query(
        models.storyFile.uri, models.storyFile.count
        ).filter(
            models.storyFile.category==categoryWord,
            models.storyFile.count<=prizeCount
            ).all()
    
    print(query)
    result = {}
    for item in query:
        uri = item[0]
        prize = item[1]
        if prize in result:
            result[prize].append(uri)
        else:
            result[prize] = [uri]
    
    print(result)
    
    return result       #returns a dict with key as prize count, and value is list of uris associated

@app.get("/getAStory")    #gives whole branch
def home(
    cate: int,          #category of the 4 in json
    prizeCount: int,     #Counter for the prize count they are on
    db: Session = Depends(get_db)   #access to db session
):
    with open('category.json') as f:
        d = json.load(f)
        categoryWord = d[str(cate)]
    
    query = db.query(
        models.storyFile.uri, models.storyFile.count
        ).filter(
            models.storyFile.category==categoryWord,
            models.storyFile.count==prizeCount
            ).all()
    
    result = [q[0] for q in query]
    print(result)
    
    return result       #list

@app.get("/")
def home(
    db: Session = Depends(get_db)   #access to db session
):
    f = db.query(models.audioFile).all()
    print(f)
    print("hi")
    return {"Success": "connected"}