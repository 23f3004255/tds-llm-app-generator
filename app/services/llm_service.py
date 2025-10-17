import json
import os
import base64
import re
import xml.etree.ElementTree as ET
from app.logger import get_logger
log = get_logger(__name__)




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
    You must respond **strictly in valid JSON format**:
    - Include commas between all fields.
    {{
      "files": [
        {{
          "path": "relative/path/to/file",
          "language": "python|javascript|html|css|...etc",
          "content": "full file content here, inside a double-quoted string"
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


# building XML prompt for better structure and multi-file handling

def build_prompt_xml(task_description, attachments, checks, round_number, previous_context=None):
    """
    Builds a structured XML prompt for LLM-based code generation (robust version).
    Designed to ensure valid XML output for multi-file applications.
    """

    prompt = f"""
    <instruction>
      <role>
        You are an expert software engineer and full-stack developer with production experience in HTML, CSS, JS, Python, and modern frameworks.
      </role>

      <objective>
        Your job is to generate or update a complete deployable application based on the user's input and round information below.
      </objective>

      <round_info>
        <current_round>{round_number}</current_round>
        <rules>
          <rule>If round = 1, build the entire project from scratch.</rule>
          <rule>If round &gt; 1, update or modify the existing project according to the new instructions while keeping previous functionalities intact.</rule>
          <rule>Ensure that the project runs correctly on GitHub Pages or via the provided run command.</rule>
        </rules>
      </round_info>

      <task_description><![CDATA[
      {task_description}
      ]]></task_description>

      <attachments><![CDATA[
      {attachments}
      ]]></attachments>

      <evaluation_criteria><![CDATA[
      {checks}
      ]]></evaluation_criteria>

      <context><![CDATA[
      {previous_context or "No previous code. This is the first round."}
      ]]></context>

      <output_format>
        Respond strictly in the following XML structure:
        <response>
          <file>
            <path>relative/path/to/file</path>
            <language>html|css|javascript|python|etc</language>
            <content><![CDATA[
                full file content here (complete code, no truncation)
            ]]></content>
          </file>
          ...
          <run_command>command to run app, if any (e.g. python app.py, npm start, etc.)</run_command>
        </response>
      </output_format>

      <rules>
        <rule>Each file must be complete and ready to run.</rule>
        <rule>Do not omit imports or boilerplate.</rule>
        <rule>Maintain consistent indentation and syntax.</rule>
        <rule>Use clean, modular, and efficient code.</rule>
        <rule>When modifying existing code, only update necessary parts.</rule>
        <rule>Generate README.md — must look professional and concise.</rule>
        <rule>Do not include any explanations, markdown, comments, or text outside &lt;response&gt; tags.</rule>
        <rule>Do not use ellipses ("...") or placeholder code.</rule>
      </rules>

      <deployment_rules>
        <rule>All generated files must be in the project root unless specified.</rule>
        <rule>The entry point must be index.html (for GitHub Pages).</rule>
        <rule>Use relative paths for assets (./style.css, ./script.js, etc.).</rule>
        <rule>If backend, ensure the run command works (e.g. FastAPI, Flask).</rule>
        <rule>Each file must be syntactically complete and production-ready.</rule>
      </deployment_rules>

      <generate>Generate your output now inside the &lt;response&gt; block only.</generate>
    </instruction>
    """

    return prompt.strip()



def save_llm_output(response_json, base_dir=os.path.join(os.getcwd(), "generated_app")):
    if not response_json:
        log.info("Empty response_json received — skipping save.")
        return

    # --- Clean LLM-style formatting (remove ```json or ``` fences) ---
    cleaned_json = re.sub(r"```(?:json)?", "", response_json).strip("` \n")

    # --- Try parsing JSON safely ---
    try:
        data = json.loads(cleaned_json)
    except json.JSONDecodeError as e:
        log.info("Invalid JSON received.")
        log.info(f"Error details: {e}")
        snippet = cleaned_json[:500]
        log.info(f"\n--- JSON Snippet Preview ---\n{snippet}\n----")
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
            log.info(f"Some error occurred while saving {file['path']}: {e}")

    log.info(f"Files saved successfully in: {base_dir}")

    run_cmd = data.get("run_command")
    if run_cmd:
        log.info(f"Run Command: {run_cmd}")



def save_llm_output_xml(response_xml, base_dir=os.path.join(os.getcwd(), "generated_app")):
    if not response_xml:
        log.info("Empty response_xml received — skipping save.")
        return

    # --- Clean LLM-style formatting (remove ```xml or ``` fences) ---
    cleaned_xml = re.sub(r"```(?:xml)?", "", response_xml).strip("` \n")

    # --- If multiple <response> roots exist, wrap them in a single <root> ---
    if cleaned_xml.count("<response") > 1:
        cleaned_xml = f"<root>{cleaned_xml}</root>"

    # --- Try parsing XML safely ---
    try:
        root = ET.fromstring(cleaned_xml)
    except ET.ParseError as e:
        log.info("Invalid XML received.")
        log.info(f"Error details: {e}")
        snippet = cleaned_xml[:500]
        log.info(f"\n--- XML Snippet Preview ---\n{snippet}\n----")
        return

    # --- Create output base directory ---
    os.makedirs(base_dir, exist_ok=True)

    # --- Iterate through all <response> tags (or root if only one) ---
    responses = root.findall("response") if root.tag == "root" else [root]

    for resp in responses:
        for file_elem in resp.findall("file"):
            try:
                path = file_elem.findtext("path")
                content = file_elem.findtext("content") or ""
                language = (file_elem.findtext("language") or "").lower()

                if not path:
                    continue

                file_path = os.path.join(base_dir, path)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)

                # --- Save file content ---
                if language == "binary":
                    with open(file_path, "wb") as f:
                        f.write(base64.b64decode(content))
                else:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(content.strip())

                log.info(f"✅ Saved: {path}")

            except Exception as e:
                log.info(f"⚠️ Error saving {path}: {e}")

        run_cmd_elem = resp.find("run_command")
        if run_cmd_elem is not None and run_cmd_elem.text:
            log.info(f"Run Command: {run_cmd_elem.text.strip()}")

    log.info(f"🎯 Files saved successfully in: {base_dir}")