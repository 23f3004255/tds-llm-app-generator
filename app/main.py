import os
import uuid
from fastapi import FastAPI, BackgroundTasks, HTTPException, Response
from app.utils import check_secret
from app.model import User_json
from dotenv import load_dotenv
from app.background import build_and_deploy
from app.logger import get_logger


load_dotenv()


log = get_logger(__name__)


app = FastAPI()



@app.post("/api/generate-app")
async def generate_app(data:User_json,background_tasks:BackgroundTasks):
    log.info("Received request to generate app.")
    log.info("Checking secret...")
    if not check_secret(data.secret, os.getenv("SECRET_KEY")):
        raise HTTPException(status_code=401, detail="Invalid secret")
    
    job_id = str(uuid.uuid4())
    log.info(f"Starting background task for job_id: {job_id}")
    background_tasks.add_task(build_and_deploy, data, job_id)
    return Response(status_code=200)
