from app.logger import get_logger

log = get_logger(__name__)

def check_secret(user_secret: str,own_secret: str) -> bool:
    log.info("Checking secret...")
    if user_secret == own_secret:
        return True
    else :
        return False