import requests


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