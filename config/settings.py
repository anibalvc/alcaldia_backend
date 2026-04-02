import os
from dotenv import load_dotenv

load_dotenv()

class Settings:

    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "mysql_db")
    MYSQL_PORT: int = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_DATABASE: str = os.getenv("MYSQL_DATABASE", "bienes")
    MYSQL_USER: str = os.getenv("MYSQL_USER", "bienes_user")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "bienes_password")
    MYSQL_ROOT_PASSWORD: str = os.getenv("MYSQL_ROOT_PASSWORD", "rootpassword")

    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"

    BACKEND_HOST: str = os.getenv("BACKEND_HOST", "0.0.0.0")
    BACKEND_PORT: int = int(os.getenv("BACKEND_PORT", "8000"))
    BACKEND_DEBUG: bool = os.getenv("BACKEND_DEBUG", "false").lower() == "true"
    BACKEND_RELOAD: bool = os.getenv("BACKEND_RELOAD", "false").lower() == "true"

    SECRET_KEY: str = os.getenv("SECRET_KEY", "desarrollo_no_usar_en_produccion")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))

    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    def __post_init__(self):
        if self.ENVIRONMENT == "production" and self.SECRET_KEY == "desarrollo_no_usar_en_produccion":
            raise ValueError("¡ADVERTENCIA! Debes cambiar SECRET_KEY en producción")

    PMA_HOST: str = os.getenv("PMA_HOST", "mysql_db")
    PMA_USER: str = os.getenv("PMA_USER", "bienes_user")
    PMA_PASSWORD: str = os.getenv("PMA_PASSWORD", "bienes_password")

settings = Settings()
