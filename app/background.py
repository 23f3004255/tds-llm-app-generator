from app.model import User_json
import json
from app.services import save_llm_output,save_llm_output_v2, ask_aipipe, build_prompt
from app.utils import clear_generated_app_folder_except_git
from dotenv import load_dotenv
import os

load_dotenv()

def generate_app(data:User_json):
    prompt = build_prompt(
        task_description=data.brief,
        attachments=data.attachments,
        checks=data.checks,
        round_number=data.round
        )
    response = None
    try:
        response=ask_aipipe(prompt,os.getenv("AIPIPE_TOKEN"))
    except Exception as e:
        print(f"Some error occured in LLM Service: {e}")
    clear_generated_app_folder_except_git(os.path.join(os.getcwd(),"generated_app"))
    try:
        save_llm_output_v2(response_json=response)
    except Exception as e:
        print(f"Some error occured in saving file: {e}")



def build_and_deploy(data:User_json,task_id: str):
    print(f"Starting task {task_id}...")
    generate_app(data)
    print(f"Task {task_id} completed.")
