from fastapi import FastAPI, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from fastapi.responses import FileResponse

# github

from contextlib import asynccontextmanager
import os
import datetime
import json
import random

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
            stringS = sound.replace(".wav", "").split("_")
            offsetTime = int(stringS[2]) - 1
            timeStampS = datetime.datetime(int(stringS[0][:4]), int(stringS[0][4:6]), int(stringS[0][6:]), int(stringS[1][:2]), int(stringS[1][2:4]), int(stringS[1][4:]))
            timeStampS = timeStampS + datetime.timedelta(minutes=offsetTime)    #Change this if we change to minute files
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


    current_path = os.getcwd()
    target_path = os.path.join("static", "stories")
    os.chdir(target_path)
    sto = os.listdir()

    if num_sound != len(sto):
        for p in sto:
            stringS = p.split(".")[0]           ##names with no dots
            c = d[stringS.split("_")[-1]]

            if p.split(".")[1] == "txt":
                typeURI = "textUri"
            else:
                typeURI = "imageUri"    #column name depending on type of file

            if db.query(models.storyFile).filter_by(count=int(stringS.split("_")[-2]),category=c).count() == 0: #none from this prize lvl
                completeJ = {typeURI:"/story/{}".format(p), "count":int(stringS.split("_")[-2]), "category":c}
                db.add(models.storyFile(**completeJ))
                db.commit()
            else:   #already exists
                db.query(models.storyFile).filter_by(count=int(stringS.split("_")[-2]),category=c).update({typeURI:"/story/{}".format(p)})
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
    startTime: str,     # 110207 -> 11.02 am 7 seconds
    duration: int,      # 60 -> 60 mins = 1hr
    locationG: int,      # 2 -> location number
    db: Session = Depends(get_db)   #access to db session
):
    
    emptyQuery = True
    while emptyQuery:

        start = datetime.datetime.now()
        start = start.replace(hour=int(str(startTime)[0:2]), minute=int(str(startTime)[2:4]), second=int(str(startTime)[4:]), microsecond=0)
        if duration==0:
            duration = 5
            print("duration is 0")
        end = start + datetime.timedelta(minutes=duration)  #adding minutes
        endString = end.strftime('%Y-%m-%d %H%M%S')
        endString = endString.split(" ")[1]
        if start.date()!=end.date():
            differentDays = True    #goes across 2 days, 11pm 3hrs
        else:
            differentDays = False   #single day, 10am 1 hr

        query = db.query(           #getting all the timestamps for the timeframe
            func.date(models.audioFile.timeStamp)
            ).filter(
                func.extract('hour', models.audioFile.timeStamp) * 3600 +
                func.extract('minute', models.audioFile.timeStamp) * 60 +
                func.extract('second', models.audioFile.timeStamp) >= int(str(startTime)[0:2]) *3600 + int(str(startTime)[2:4]) * 60  + int(str(startTime)[4:]), 
                func.extract('hour', models.audioFile.timeStamp) * 3600 +
                func.extract('minute', models.audioFile.timeStamp) * 60 +
                func.extract('second', models.audioFile.timeStamp) <= int(str(endString)[0:2]) *3600 + int(str(endString)[2:4]) * 60  + int(str(endString)[4:]),
                models.audioFile.location == locationG
                ).distinct().order_by(func.date(models.audioFile.timeStamp)).all()
        print("bye")


        if len(query)==0:   #Alison's random feature
            print("not found")
            random_entry = db.query(models.audioFile).order_by(func.random()).first()
            if not random_entry:
                return "no entries in audio DB"
            timeString = (random_entry.timeStamp.strftime("%H%M%S"))
            startTime = timeString
            locationG = random_entry.location
        else:
            print("found")
            emptyQuery = False
    
    if differentDays and len(query)>1:
        query.pop() #getting rid of largest from randomiser, so can't have 11.59pm on the last day, won't cause only 1 min of audio
    
    chosenDate = str(random.choice(query))
    chosenDate = chosenDate.replace("(","").replace("'","").replace(",","").replace(")","")
    chosenDate = chosenDate.split("-")
    targetDate = datetime.date(int(chosenDate[0]), int(chosenDate[1]), int(chosenDate[2]))

    if differentDays:       # cross over night 11.59pm to 1am next day
        secondDay = targetDate + datetime.timedelta(days=1)
        ##### From time to midnight
        query = db.query(           #after start time, before end time
        models.audioFile.uri,models.audioFile.timeStamp
        ).filter(
            func.date(models.audioFile.timeStamp) == targetDate,
            func.extract('hour', models.audioFile.timeStamp) * 3600 +
            func.extract('minute', models.audioFile.timeStamp) * 60 +
            func.extract('second', models.audioFile.timeStamp) >= int(str(startTime)[0:2]) *3600 + int(str(startTime)[2:4]) * 60  + int(str(startTime)[4:]), 
            func.extract('hour', models.audioFile.timeStamp) * 3600 +
            func.extract('minute', models.audioFile.timeStamp) * 60 +
            func.extract('second', models.audioFile.timeStamp) <= 24 *3600,          # 24 hr clock, midnight
            models.audioFile.location == locationG
            ).all()
        
        query.append(db.query(           #after start time, before end time
        models.audioFile.uri,models.audioFile.timeStamp
        ).filter(
            func.date(models.audioFile.timeStamp) == secondDay,
            func.extract('hour', models.audioFile.timeStamp) * 3600 +
            func.extract('minute', models.audioFile.timeStamp) * 60 +
            func.extract('second', models.audioFile.timeStamp) >= 0,        #midnight, 0 seconds
            func.extract('hour', models.audioFile.timeStamp) * 3600 +
            func.extract('minute', models.audioFile.timeStamp) * 60 +
            func.extract('second', models.audioFile.timeStamp) <= int(str(endString)[0:2]) *3600 + int(str(endString)[2:4]) * 60  + int(str(endString)[4:]),
            models.audioFile.location == locationG
            ).all())
        ##### From midnight to time
    else:
        ## doesn't cross days!
        query = db.query(           #after start time, before end time
        models.audioFile.uri,models.audioFile.timeStamp
        ).filter(
            func.date(models.audioFile.timeStamp) == targetDate,
            func.extract('hour', models.audioFile.timeStamp) * 3600 +
            func.extract('minute', models.audioFile.timeStamp) * 60 +
            func.extract('second', models.audioFile.timeStamp) >= int(str(startTime)[0:2]) *3600 + int(str(startTime)[2:4]) * 60  + int(str(startTime)[4:]), 
            func.extract('hour', models.audioFile.timeStamp) * 3600 +
            func.extract('minute', models.audioFile.timeStamp) * 60 +
            func.extract('second', models.audioFile.timeStamp) <= int(str(endString)[0:2]) *3600 + int(str(endString)[2:4]) * 60  + int(str(endString)[4:]),
            models.audioFile.location == locationG
            ).all()
        
    if len(query)==0:
        return "empty query"

    result = {"audioChunks":[], "date":targetDate.strftime("%Y-%m-%d")}
    for q in query:
        result["audioChunks"].append(q[0]) # add uri to audioChunks
    result = json.dumps(result)
    return result

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
        models.storyFile
        ).filter(
            models.storyFile.category==categoryWord,
            models.storyFile.count<=prizeCount
            ).all()
    
    if len(query)==0:
        return "It is empty"
    
    result = {"stories":[]}
    for obj in query:
        pass
        a = {"count": obj.count, "imageUri":obj.imageUri, "textUri":obj.textUri}
        result["stories"].append(a)
    
    return json.dumps(result)       #returns a dict with key as prize count, and value is list of uris associated

@app.get("/getNumStory")
def numStory(db: Session = Depends(get_db)):
    final = {"numStories":[]}
    with open('category.json') as f:
        categoryjson = json.load(f)
        category = categoryjson.keys()
        for k in category:
            name = categoryjson[k]  #name of branch
            query = db.query(
                models.storyFile.count
                ).filter(
                    models.storyFile.category==name
                    ).all()
            biggest = max(query)[0]
            typ = {"category":int(k), "number":biggest}  #this all under assumption
            final["numStories"].append(typ)

    return json.dumps(final)

@app.get("/getAStory")    #gives whole branch, #CHANGE THIS SOPHIE
def home(
    cate: int,          #category of the 4 in json
    prizeCount: int,     #Counter for the prize count they are on
    db: Session = Depends(get_db)   #access to db session
):
    with open('category.json') as f:
        d = json.load(f)
        if str(cate) in d:
            categoryWord = d[str(cate)]
        else:
            return "Category not valid"
    
    query = db.query(
        models.storyFile
        ).filter(
            models.storyFile.category==categoryWord,
            models.storyFile.count==prizeCount
            ).all()
    
    if len(query)==0:
        return "It is empty"
    elif len(query)>1:
        return "multiple entries in the database for a given category and count, check database"
    obj = query[0]
    result = {"count": obj.count, "imageUri":obj.imageUri, "textUri":obj.textUri}
    
    return json.dumps(result)     #list

@app.get("/getRandomSvg")    #gives whole branch, #CHANGE THIS SOPHIE
def randomSvg(
    db: Session = Depends(get_db)   #access to db session
):
    cate = 1    #hard coded to 1, 1 will always be Symbols
    #prizeCount needs to be random
    with open('category.json') as f:
        d = json.load(f)
        if str(cate) in d:
            categoryWord = d[str(cate)]
        else:
            return "Category not valid, check JSON, 1 should be Symbols"
    
    query = db.query(
        models.storyFile
        ).filter(
            models.storyFile.category==categoryWord
            ).order_by(func.random()).first()     #gets random image
    
    result = {"imageUri":query.imageUri}
    
    return json.dumps(result)     #list


@app.get("/")
def home(
    db: Session = Depends(get_db)   #access to db session
):
    return {"Success": "connected"}
