from app.model import User_json
import json
from app.services import save_llm_output_v2, ask_aipipe, build_prompt
from app.services.github_service_2 import push_to_github
from app.utils import clear_generated_app_folder_by_round, load_context, save_context
from dotenv import load_dotenv
import os

load_dotenv()

def generate_app(data: User_json):
    context_file = os.path.join(os.getcwd(), "app", "data", "context.json")

    # Step 1: Clean generated_app folder
    clear_generated_app_folder_by_round(folder_path=os.path.join(os.getcwd(), "generated_app"),round_number=data.round)

    # Step 2: Determine context based on round
    previous_context = None
    if data.round > 1:
        previous_context = load_context()

    # Step 3: Build the prompt
    prompt = build_prompt(
        task_description=data.brief,
        attachments=data.attachments,
        checks=data.checks,
        round_number=data.round,
        previous_context=previous_context
    )

    # Step 4: Call the LLM
    response = None
    try:
        response = ask_aipipe(prompt, os.getenv("AIPIPE_TOKEN"))
    except Exception as e:
        print(f"❌ Some error occurred in LLM Service: {e}")
        return

    # Step 5: Clear generated folder again before saving new output
    clear_generated_app_folder_by_round(folder_path=os.path.join(os.getcwd(), "generated_app"),
                                        round_number=data.round
                                        )

    # Step 6: Save the LLM-generated files
    try:
        save_llm_output_v2(response_json=response)
    except Exception as e:
        print(f"❌ Some error occurred in saving files: {e}")

    # Step 7: Save current response as context for next round
    try:
        save_context(response, round_number=data.round)
    except Exception as e:
        print(f"⚠️ Failed to save context: {e}")


# def push_code_to_github():
#     repo_dir = os.path.join(os.getcwd(), "generated_app")
#     remote_url = f"https://{os.getenv('GITHUB_USERNAME')}:{os.getenv('GITHUB_TOKEN')}@github.com/{os.getenv('GITHUB_USERNAME')}/tds-llm-project.git"
#     git_push_repo()




def build_and_deploy(data:User_json,task_id: str):
    print(f"Starting task {task_id}...")
    generate_app(data)
    links=push_to_github(task_id=data.task, round_number=data.round, base_dir="generated_app")
    print(links)
    print(f"Task {task_id} completed.")
