import os
import platform


class Config:
    SECRET_KEY = (
        os.environ.get("SECRET_KEY")
        or "you-will-never-guess:6d667eac81ee0897e67cecbaf10a801ee789f06a2e9849e46cd28728"
    )
    DEBUG = False
    HOST = "127.0.0.1"
    PORT = 80
    SCANNER_OUT_DIR = "output"
    OUTPUT_DIR_VAR_NAME = "SCANNER_OUT_DIR"

    CELERY_BROKER_URL = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND = "redis://localhost:6379/0"

    if platform.system() == "Darwin":  # MacOS coz i work on
        ENV = "development"
    elif platform.system() == "Linux":
        ENV = "production"
    else:
        ENV = "testing"


class DevelopmentConfig(Config):
    DEBUG = True
    PORT = 8080
    LOGIN_REQUIRED = True
    USERNAME = "p"
    PASSWORD = "p"


class ProductionConfig(Config):
    DEBUG = False
    LOGIN_REQUIRED = True
    PORT = 8009
    USERNAME = "p"
    PASSWORD = "p"


class TestingConfig(Config):
    DEBUG = True
    LOGIN_REQUIRED = False
    PORT = 8080
    USERNAME = "p"
    PASSWORD = "p"


def get_config(env=None):
    env = env or os.getenv("FLASK_ENV", "production").lower()
    if env == "development":
        return DevelopmentConfig()
    elif env == "testing":
        return TestingConfig()
    else:
        return ProductionConfig()
