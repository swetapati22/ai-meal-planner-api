"""
Configuration management using Pydantic Settings
"""
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    #Application
    app_name: str = "AI Meal Planner API"
    app_version: str = "1.0.0"
    debug: bool = True
    log_level: str = "INFO"
    #Options: DEBUG, INFO, WARNING, ERROR
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8001
    
    # LLM Configuration
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    
    # Caching
    cache_ttl_hours: int = 24
    enable_cache: bool = True
    
    # Rate Limiting
    rate_limit_enabled: bool = False
    rate_limit_requests_per_minute: int = 60
    
    # Query Parser Configuration
    enable_llm_validation: bool = True  #Enable LLM validation of regex extraction:
    enable_query_dump: bool = True  #Enable saving query parsing data dumps:
    
    class Config: #Special Pydantic class for configuration options. It tells Pydantic where to find the environment variables.
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()

