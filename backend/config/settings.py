import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

from pathlib import Path
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

class Settings(BaseSettings):
    PROJECT_NAME: str = "Agentic B2B Outbound Sales Automation System"
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    NEON_DB_URL: str = os.getenv("NEON_DB_URL", "")
    LANGCHAIN_API_KEY: str = os.getenv("LANGCHAIN_API_KEY", "")
    LANGCHAIN_TRACING_V2: str = os.getenv("LANGCHAIN_TRACING_V2", "false")
    LANGCHAIN_PROJECT: str = os.getenv("LANGCHAIN_PROJECT", "company-outreach-agent")
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")
    EMAIL_HOST: str = os.getenv("EMAIL_HOST", "smtp.gmail.com")
    EMAIL_PORT: int = int(os.getenv("EMAIL_PORT", "587"))
    EMAIL_USER: str = os.getenv("EMAIL_USER", "")
    EMAIL_PASSWORD: str = os.getenv("EMAIL_PASSWORD", "")
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "vinaykumarreddy8374@gmail.com")
    IMAP_HOST: str = os.getenv("IMAP_HOST", "imap.gmail.com")
    TARGET_EMAIL: str = os.getenv("TARGET_EMAIL", "")
    TARGET_PASSWORD: str = os.getenv("TARGET_PASSWORD", "")
    APOLLO_API_KEY: str = os.getenv("APOLLO_API_KEY", "")

    class Config:
        case_sensitive = True

settings = Settings()
