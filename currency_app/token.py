from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from currency_app import models
from datetime import datetime, timedelta
from fastapi import HTTPException, status


SECRET_KEY = "09d25e094faa"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 180


def return_headers(access_token):
    content = {"access_token": access_token}
    response = JSONResponse(content=content)
    # Устанавливаем заголовок 'Authorization' с токеном в ответе
    response.headers['Authorization'] = f"Bearer {access_token}"

    return response


def check_tokens(db: Session, token: str):
    """
    Проверяет access токен и refresh токен на истечение срока действия.
    Возвращает новый access токен, если refresh токен действителен.
    """

    access_payload = verify_token(token, SECRET_KEY, [ALGORITHM])
    
    if access_payload is None:
        return {"error": "bad token"}

    if access_payload and access_payload.get("exp") > datetime.utcnow().timestamp():
        # Access токен действителен
        return token

    # Проверяем refresh токен, если access токен истек
    user_token_obj = get_refresh_token(db, access_payload.get("id"))

    refresh_token = user_token_obj.token

    refresh_payload = verify_token(refresh_token, SECRET_KEY, [ALGORITHM])
    if refresh_payload and refresh_payload.get("exp") > datetime.utcnow().timestamp():
        # Refresh токен действителен, создаем новый access токен
        user_id = refresh_payload.get("id")
        user = models.User.get_by_id(db, user_id)

        if user is None:
            return {"error": "User not found"}
        
        new_token = create_tokens(user, False, db)
        return new_token

    # И access, и refresh токены истекли
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)


def verify_token(token: str, secret_key: str, algorithms: str):
    """
    Проверяет токен и возвращает payload токена, если токен действителен.
    """
    try:
        payload = jwt.decode(token, secret_key, algorithms=algorithms)
        return payload
    except JWTError:
        return None
    

def get_refresh_token(db: Session, user_id: str):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if user_id is None:
        raise credentials_exception
    token = db.query(models.Token).filter(models.User.usr_id == user_id).first()
    if token is None:
        raise credentials_exception
    return token

    
def create_tokens(user, need_refresh=False, db=None):

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    date = datetime.utcnow()

    # Создание токенов
    access_token_payload = {"id": str(user.id), "exp": date + access_token_expires}
    access_token = jwt.encode(access_token_payload, SECRET_KEY, algorithm=ALGORITHM)

    if need_refresh:
        refresh_token_payload = {"id": str(user.id), "exp": date + refresh_token_expires}
        refresh_token = jwt.encode(refresh_token_payload, SECRET_KEY, algorithm=ALGORITHM)

        db_token = models.Token(user_id=user.id, token=refresh_token)
        db.add(db_token)
        db.commit()
        db.refresh(db_token)

    return access_token