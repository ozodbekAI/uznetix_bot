# config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    
    BOT_TOKEN: str
    BOT_NAME: str = "Uznetix Advisor"
    
    GETCOURSE_SECRET_KEY: str
    GETCOURSE_API_URL: str = "https://uznetix.getcourse.ru/pl/api"
    

    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-5o-mini"
    OPENAI_MAX_TOKENS: int = 1500
    OPENAI_TEMPERATURE: float = 0.7
    
    DATABASE_URL: str
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    
    REDIS_URL: str
    REDIS_TTL: int = 3600 
    
    # Admin settings
    ADMIN_IDS: str = "7166331865"
    
    # Application settings
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    OPENAI_JSON_MODE: bool = True
    
    MAX_INTERVIEW_QUESTIONS: int = 10
    MIN_INTERVIEW_QUESTIONS: int = 8
    SESSION_TIMEOUT: int = 3600
    

    MAX_STOCK_RECOMMENDATIONS: int = 3
    ENABLE_BONDS: bool = True
    ENABLE_ETF: bool = True
    ENABLE_CURRENCY: bool = True
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )
    
    @property
    def admin_ids_list(self) -> List[int]:
        """Parse admin IDs from string to list"""
        if not self.ADMIN_IDS:
            return []
        return [int(id.strip()) for id in self.ADMIN_IDS.split(",") if id.strip()]
    
    @property
    def is_debug(self) -> bool:
        """Check if debug mode is enabled"""
        return self.DEBUG


settings = Settings()