from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
# from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse

from contextlib import asynccontextmanager
import os
import datetime

from .database import SessionLocal, engine
from . import models

# Use migrations normally
models.Base.metadata.create_all(bind=engine)
app = FastAPI()

# app.mount("/static", StaticFiles(directory="static"), name="static")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

        ##12.10 video

@asynccontextmanager
async def lifespan(app: FastAPI):
    db = SessionLocal()
    num_sound = db.query(models.audioFile).count()

    current_path = os.getcwd()  # Get current working directory
    # parent_path = os.path.dirname(current_path)  # Move up one level
    target_path = os.path.join("static", "tenSecChunks")  # Construct the path
    os.chdir(target_path)
    print(target_path)
    songs = os.listdir()
    print(len(songs))

    if num_sound != len(songs):      #static file number == db number
        for sound in os.listdir():
            stringS = sound.replace(".WAV", "").split("_")
            offsetTime = int(stringS[2])-10  #10 is the first one, so -10
            timeStampS = datetime.datetime(int(stringS[0][:4]), int(stringS[0][4:6]), int(stringS[0][6:]), int(stringS[1][:2]), int(stringS[1][2:4]), int(stringS[1][4:]))
            timeStampS = timeStampS + datetime.timedelta(seconds=offsetTime)
            
            locationS = stringS[3]   #location it's from
            if db.query(models.audioFile).filter_by(uri="/tenSecChunks/{}".format(sound)).count() == 0:
                completeJ = {"timeStamp": timeStampS, "uri":"/tenSecChunks/{}".format(sound), "location":locationS}
                db.add(models.audioFile(**completeJ))
            db.commit() 
    ### added to db, NOW: table for stories?
    # I havent dealt with deletion of songs, only adding
    db.close()
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/playIt")
def tryPlay():
    def iterfile():
        p = "C:/Part 1B/GroupProject/forestAPI/visiting-the-forest-stream-api/static/tenSecChunks/20230512_102258_10_1.WAV"
        with open(p, mode="rb") as file_like:
            yield from file_like

    return StreamingResponse(iterfile(), media_type="audio/WAV")

@app.get("/")
def home(
    db: Session = Depends(get_db)   #access to db session
):
    f = db.query(models.audioFile).all()
    print(f)
    print("hi")
    return {"Success": "connected"}