import os

DATA_PATH = os.path.join(os.getcwd(), "StarRailTools")

APP_CONFIG_PATH = os.path.join(DATA_PATH, "config")

APP_LOG_PATH = os.path.join(DATA_PATH, "log")

GAME_RUNTIME_LOG_PATH = os.path.join(os.getenv("USERPROFILE"), "AppData", "LocalLow")

TIMEOUT = 5

OPEN = True

CLOSE = False

MAX_MENU_LENGTH = 40
