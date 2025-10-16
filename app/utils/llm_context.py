import os
import json
from app.logger import get_logger

log = get_logger(__name__)

CONTEXT_PATH = os.path.join(os.getcwd(), "app", "data", "context.json")


def save_context(context: str, round_number: int) -> None:
    """
    Save the full LLM response (as JSON) to a context file.
    Clears any previous context if it's the first round.
    """

    # Ensure directory exists
    os.makedirs(os.path.dirname(CONTEXT_PATH), exist_ok=True)

    # If round 1 → clear old context
    if round_number == 1 and os.path.exists(CONTEXT_PATH):
        os.remove(CONTEXT_PATH)

    try:
        # Convert JSON string to dict if possible
        if isinstance(context, str):
            try:
                context_obj = json.loads(context)
            except json.JSONDecodeError:
                # If not valid JSON, save raw string
                context_obj = {"raw_context": context}
        else:
            context_obj = context

        # Write cleanly formatted JSON
        with open(CONTEXT_PATH, "w", encoding="utf-8") as f:
            json.dump(context_obj, f, ensure_ascii=False, indent=2)

        log.info(f"Context saved successfully (round {round_number}).")

    except Exception as e:
        log.info(f"Error saving context: {e}")


def load_context() -> str | None:
    """
    Load the previous context from the context file (if any).
    Returns the JSON string (not dict) so it can be directly passed into LLM.
    """

    if not os.path.exists(CONTEXT_PATH):
        log.info("No previous context found. Starting fresh.")
        return None

    try:
        with open(CONTEXT_PATH, "r", encoding="utf-8") as f:
            data = f.read().strip()

        if not data:
            log.info("Context file is empty.")
            return None

        log.info("Loaded previous context successfully.")
        return data

    except Exception as e:
        log.info(f"Error loading context: {e}")
        return None
