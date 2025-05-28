from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:JHFGHDkjeyusfvb764&^%~@db.smhzvrzkwcyoboxrntwj.supabase.co:5432/postgres"
    
    class Config:
        env_file = ".env"

settings = Settings() 

