from jose import jwt
from sqlalchemy.orm import Session
from fastapi import Depends
from currency_app import schemas_app, models, token as token_modul
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = "09d25e094faa"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 180

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(data: dict, expire):
    to_encode = data.copy()
    # expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def authenticate_user(db: Session, username: str, password: str):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user or not user.verify_password(password):
        return False
    return user


def get_current_user(db: Session, user_id: str):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if user_id is None:
        raise credentials_exception
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user
    

def register_user(db: Session, user: schemas_app.UserCreate):
    # Проверяем, существует ли уже пользователь с таким username или email
    existing_user = db.query(models.User).filter(
        (models.User.username == user.username) | (models.User.email == user.email)
    ).first()

    # Если пользователь существует, возвращаем исключение
    if existing_user:
        # Можете заменить None на выброс исключения или возвращение ошибки
        return {"error": "Username or email address already exists."}

    # Если такого пользователя нет, продолжаем создание новой записи
    hashed_password = hash_password(user.password)
    db_user = models.User(email=user.email, username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    new_tokens = token_modul.create_tokens(db_user)

    db_token = models.Token(user_id=db_user.id, token=new_tokens['refresh_token'])
    db.add(db_token)
    db.commit()
    db.refresh(db_token)


    return {"access_token": new_tokens['access_token']}


def hash_password(password: str) -> str:
    """Возвращает хешированный пароль."""
    return pwd_context.hash(password)

