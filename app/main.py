import os
import uuid
from fastapi import FastAPI, BackgroundTasks, HTTPException
from app.utils import check_secret
from app.model import User_json
from dotenv import load_dotenv
from app.background import build_and_deploy
from app.database import save_job, load_job


load_dotenv()


app = FastAPI()



@app.post("/api/generate-app")
async def generate_app(data:User_json,background_tasks:BackgroundTasks):
    if not check_secret(data.secret, os.getenv("SECRET_KEY")):
        raise HTTPException(status_code=401, detail="Invalid secret")
    
    job_id = str(uuid.uuid4())
    save_job(job_id, "processing")
    job_status = load_job(job_id)
    background_tasks.add_task(build_and_deploy, data, job_id)
    return {"job_id": job_id, "status": job_status}
