from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from fastapi.responses import FileResponse

from contextlib import asynccontextmanager
import os
import datetime
from pathlib import Path

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
        

async def initialize_db(app: FastAPI):
    db = SessionLocal()
    num_sound = db.query(models.audioFile).count()

    current_path = os.getcwd()
    target_path = os.path.join("static", "tenSecChunks")
    os.chdir(target_path)
    songs = os.listdir()

    if num_sound != len(songs):
        for sound in songs:
            stringS = sound.replace(".WAV", "").split("_")
            offsetTime = int(stringS[2]) - 10
            timeStampS = datetime.datetime(int(stringS[0][:4]), int(stringS[0][4:6]), int(stringS[0][6:]), int(stringS[1][:2]), int(stringS[1][2:4]), int(stringS[1][4:]))
            timeStampS = timeStampS + datetime.timedelta(seconds=offsetTime)
            locationS = stringS[3]

            if db.query(models.audioFile).filter_by(uri=f"/tenSecChunks/{sound}").count() == 0:
                completeJ = {"timeStamp": timeStampS, "uri": f"/tenSecChunks/{sound}", "location": locationS}
                db.add(models.audioFile(**completeJ))
                db.commit()

    db.close()
    os.chdir(current_path)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await initialize_db(app)
    yield

app = FastAPI(lifespan=lifespan)

app.mount("/audio", StaticFiles(directory=("static/tenSecChunks")), name="audio")
app.mount("/story", StaticFiles(directory=("static/stories")), name="story")

# @app.get("/audio/{file_name}")
# async def get_audio(file_name: str):
#     return FileResponse(f"static/tenSecChunks/{file_name}")

# @app.get("/playIt")
# def tryPlay():
#     def iterfile():
#         p = "C:/Part 1B/GroupProject/forestAPI/visiting-the-forest-stream-api/static/tenSecChunks/20230512_102258_10_1.WAV"
#         with open(p, mode="rb") as file_like:
#             yield from file_like

#     return StreamingResponse(iterfile(), media_type="audio/WAV")

@app.get("/")
def home(
    db: Session = Depends(get_db)   #access to db session
):
    f = db.query(models.audioFile).all()
    print(f)
    print("hi")
    return {"Success": "connected"}