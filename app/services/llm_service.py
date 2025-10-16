import requests
import json
import os
import base64
import re
from app.logger import get_logger
log = get_logger(__name__)

def ask_aipipe(input_prompt:str,aipipe_token,model="gpt-4.1"):
    if not aipipe_token:
        raise RuntimeError("AIPIPE_TOKEN not found please provide token.")

    response = requests.post(
        "https://aipipe.org/openai/v1/responses",
        headers={
                "Authorization": f"Bearer {aipipe_token}",
                "Content-Type": "application/json"
                },
        json={
                "model": model,
                "input": input_prompt
                }
    )

    # Raise an exception if request failed
    response.raise_for_status()

    # Parse JSON
    data = response.json()

    return data["output"][0]["content"][0]["text"]


def build_prompt(task_description,attachments,checks, round_number, previous_context=None):
    """
    Builds a structured prompt for LLM-based code generation.
    """
    prompt = f"""
    You are an expert software engineer and full-stack developer.
    
    ## Objective
    Your task is to generate or update a complete application based on the user's instructions below.
    
    ## Round Information
    - Current Round: {round_number}
    - If Round = 1: Build the full project from scratch.
    - If Round > 1: Modify the existing project according to new instructions, 
      ensuring all previous functionalities continue to work.
      ensuring that tha project will run on github page.
    
    ## Task Description
    {task_description}

    ## Attachments will be encoded as data URIs
    {attachments}

    ## checks: mention how it will be evaluated
    {checks}

    
    ## Context (if available)
    {previous_context or "No previous code. This is the first round."}
    
    ## Output Format
    You must respond **strictly in JSON format**:
    {{
      "files": [
        {{
          "path": "relative/path/to/file",
          "language": "python|javascript|html|css|...etc",
          "content": "full file content here"
        }},
        ...
      ],
      "run_command": "command to run the app, if any (e.g. 'python main.py' or 'npm start')"
    }}
    
    ## Rules
    1. Each file must be complete and executable.
    2. Do not omit any required imports or boilerplate.
    3. Keep indentation and syntax consistent.
    4. Use efficient, clean, and modular code.
    5. If updating existing code, modify only what’s necessary.
    6. Avoid long explanations—return only JSON.
    7. genereate the readme.md it should be clean and professional.
    8. Do not add any explanation or commentary anywhere.
    9. Do not include comments inside JSON (like `//` or `/* ... */`)

    ## Deployment Rules
    1. **All generated files must be in the project root** — do NOT use subfolders like `/public` or `/src` unless explicitly asked.
    2. The entry file must be `index.html` in the root directory (so it works automatically on GitHub Pages).
    3. Use **relative paths** for all assets (`./style.css`, `./script.js`, etc.).
    4. If it’s a backend app (Flask, FastAPI, etc.), ensure it runs via the provided command.
    5. No placeholder text, comments, or `...` truncations in JSON.
    6. Each file must be syntactically complete and ready to execute or deploy.
    
    Generate your output now.
    """
    return prompt.strip()


def save_llm_output(response_json, base_dir=os.path.join(os.getcwd(),"generated_app")):
    data = json.loads(response_json)

    for file in data["files"]:
        file_path = os.path.join(base_dir, file["path"])
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(file["content"])

    log.info(f"Files saved in {base_dir}")
    log.info(f"Run Command: {data.get('run_command')}")




def save_llm_output_v2(response_json, base_dir=os.path.join(os.getcwd(), "generated_app")):
    if not response_json:
        log.info("⚠️ Empty response_json received — skipping save.")
        return

    # --- Clean LLM-style formatting (remove ```json or ``` fences) ---
    cleaned_json = re.sub(r"```(?:json)?", "", response_json).strip("` \n")

    # --- Try parsing JSON safely ---
    try:
        data = json.loads(cleaned_json)
    except json.JSONDecodeError as e:
        log.info("❌ Invalid JSON received.")
        log.info(f"🔍 Error details: {e}")
        snippet = cleaned_json[:500]
        log.info("\n--- JSON Snippet Preview ---\n", snippet, "\n----------------------------")
        return

    # --- Create output base directory ---
    os.makedirs(base_dir, exist_ok=True)

    # --- Save each file ---
    for file in data.get("files", []):
        try:
            file_path = os.path.join(base_dir, file["path"])
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            content = file.get("content", "")
            language = file.get("language", "").lower()

            if language == "binary":
                with open(file_path, "wb") as f:
                    f.write(base64.b64decode(content))
            else:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)

        except Exception as e:
            log.info(f"⚠️ Some error occurred while saving {file['path']}: {e}")

    log.info(f"✅ Files saved successfully in: {base_dir}")

    run_cmd = data.get("run_command")
    if run_cmd:
        log.info(f"▶️ Run Command: {run_cmd}")
