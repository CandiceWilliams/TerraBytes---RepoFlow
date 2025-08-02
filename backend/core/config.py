from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    mongodb_url: str
    gemini_api_key: str
    app_name: str = "Hackathon API"
    debug: bool = False
    
    class Config:
        env_file = ".env"

settings = Settings()