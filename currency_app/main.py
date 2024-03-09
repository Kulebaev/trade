from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from currency_app import user_app, schemas_app, models, database, currency, token as token_modul
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader

models.Base.metadata.create_all(bind=database.engine)
header_scheme = APIKeyHeader(name="authorization")

app = FastAPI()


@app.post("/register/")
def register_user_endpoint(user: schemas_app.UserCreate, db: Session = Depends(database.get_db)):
    return user_app.register_user(db=db, user=user)


@app.post("/auth")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = user_app.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    tokens = token_modul.create_tokens(user)

    access_token=tokens['access_token']

    return token_modul.return_headers(access_token)
    

@app.post("/post_currencies/")
def post_currency(data_carrency: schemas_app.Carrency, db: Session = Depends(database.get_db),authorization: str = Depends(header_scheme)):
    # Проверяем, предоставлен ли заголовок Authorization
    if authorization is None:
        raise HTTPException(status_code=401, detail="Authorization header is missing")

    # Извлекаем токен из заголовка.
    token_type, _, access_token = authorization.partition(' ')
    if token_type.lower() != "bearer" or not access_token:
        raise HTTPException(status_code=403, detail="Invalid authorization header format")
    
    try:
        token_modul.check_tokens(db, access_token)

        return currency.save_currencies(db, data_carrency)
    except HTTPException as e:
        return {"error": "Token expired, please log in again"}
    

@app.get("/currencies/")
def create_currencies(db: Session = Depends(database.get_db)):
    return currency.currencies_list(db)



@app.get("/token_upd/", response_class=JSONResponse)
def create_currencies(key: str = Depends(header_scheme), db: Session = Depends(database.get_db)):

    if key is None:
        raise HTTPException(status_code=401, detail="Authorization header is missing")

    token_type, _, access_token = key.partition(' ')
    if token_type.lower() != "bearer" or not access_token:
        raise HTTPException(status_code=401, detail="Invalid authorization header format")

    tokens = token_modul.check_tokens(db, access_token)
    print(tokens)
    return token_modul.return_headers(tokens)
