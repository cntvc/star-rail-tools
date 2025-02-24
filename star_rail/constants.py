import os
import sys

APP_NAME = "StarRailTools"

ROOT_PATH = os.path.join(os.path.dirname(sys.argv[0]), APP_NAME)

APPDATA_PATH = os.path.join(ROOT_PATH, "AppData")

TEMP_PATH = os.path.join(APPDATA_PATH, "temp")

CONFIG_PATH = os.path.join(APPDATA_PATH, "config")

LOG_PATH = os.path.join(APPDATA_PATH, "log")

DATA_PATH = os.path.join(APPDATA_PATH, "data")

IMPORT_DATA_PATH = os.path.join(ROOT_PATH, "Import")
