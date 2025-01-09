import os
import sys

APP_NAME = "StarRailTools"

####################################################################
# Path
####################################################################

ROOT_PATH = os.path.dirname(sys.argv[0])

# AppData ---------------------------------------------------------

APPDATA_PATH = os.path.join(ROOT_PATH, "AppData")

TEMP_PATH = os.path.join(APPDATA_PATH, "temp")

LOG_PATH = os.path.join(APPDATA_PATH, "log")

DATA_PATH = os.path.join(APPDATA_PATH, "data")

# UserData ---------------------------------------------------------

USERDATA_PATH = os.path.join(ROOT_PATH, "UserData")

IMPORT_DATA_PATH = os.path.join(USERDATA_PATH, "Import")
