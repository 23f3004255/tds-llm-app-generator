def check_secret(user_secret: str,own_secret: str) -> bool:
    if user_secret == own_secret:
        return True
    else :
        return False