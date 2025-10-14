from app.model import User_json
import json


def build_and_deploy(data:dict,task_id: str):
    user_data = json.dumps(data)
    print(user_data["secret"])
