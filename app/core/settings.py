from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY:str 
    ALGORITHM:str
    ACCESS_TOKEN_EXPIRE_MINUTES:int 
    REFRESH_TOKEN_EXPIRE_DAYS:int 
    NEXTJS_URL:str
    DATABASE_URL:str

    class Config:
        env_file = ".env"


settings = Settings()

    
    