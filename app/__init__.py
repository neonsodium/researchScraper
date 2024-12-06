import os

from flask import Flask

from app.celery_utils import make_celery
from config import Config, DevelopmentConfig, ProductionConfig, TestingConfig

app = Flask(__name__)


if Config.ENV == "development":
    app.config.from_object(DevelopmentConfig)
elif Config.ENV == "production":
    app.config.from_object(ProductionConfig)
elif Config.ENV == "testing":
    app.config.from_object(TestingConfig)

try:
    app.config[Config.OUTPUT_DIR_VAR_NAME] = Config.SCANNER_OUT_DIR
    os.makedirs(os.path.join(os.getcwd(), app.config[Config.OUTPUT_DIR_VAR_NAME]), exist_ok=True)
except OSError:
    print(OSError)


# first import config and then call make_celery
celery = make_celery(app)
# TODO move it
# from app.app_routes import main_routes
