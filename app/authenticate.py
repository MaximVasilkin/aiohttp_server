from bcrypt import hashpw, gensalt, checkpw


def get_hashed_password(password: str):
    password = password.encode()
    password = hashpw(password, salt=gensalt())
    password = password.decode()
    return password


def check_password(password: str, hashed_password: str) -> bool:
    return checkpw(password.encode(), hashed_password.encode())
