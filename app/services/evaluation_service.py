import time
import requests

def post_evaluation(evaluation_url: str, payload: dict, max_total_seconds: int = 600):
    """
    Send task result to evaluation URL with exponential backoff,
    ensuring the total process (all retries + delays) completes within `max_total_seconds`.
    """
    start_time = time.time()
    delay = 1  # initial backoff delay (1s)
    attempt = 0

    while True:
        attempt += 1
        try:
            response = requests.post(
                evaluation_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            if response.status_code == 200:
                print("✅ Successfully submitted to evaluation endpoint!")
                return True
            else:
                print(f"⚠️ Attempt {attempt}: HTTP {response.status_code} — {response.text[:200]}")
        except Exception as e:
            print(f"⚠️ Attempt {attempt}: Exception — {e}")

        # check remaining time
        elapsed = time.time() - start_time
        remaining = max_total_seconds - elapsed

        if remaining <= 0:
            print("❌ Failed to submit within 10 minutes (time limit reached)")
            return False

        # Adjust delay to never exceed remaining time
        next_delay = min(delay, remaining)
        print(f"⏱ Retrying in {next_delay:.1f}s... (elapsed: {elapsed:.1f}s)")
        time.sleep(next_delay)

        delay = min(delay * 2, 120)  # exponential backoff capped at 2 minutes
