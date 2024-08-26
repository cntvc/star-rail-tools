import os
import sys

APP_NAME = "StarRailTools"

####################################################################
# path
####################################################################

ROOT_PATH = os.path.dirname(sys.argv[0])

# AppData ----------------------------------------------------------

APPDATA_PATH = os.path.join(ROOT_PATH, "AppData")
"""保存软件运行数据的根目录"""

TEMP_PATH = os.path.join(APPDATA_PATH, "temp")

CONFIG_PATH = os.path.join(APPDATA_PATH, "config")

LOG_PATH = os.path.join(APPDATA_PATH, "log")

DATA_PATH = os.path.join(APPDATA_PATH, "data")

# UserData ----------------------------------------------------------

USERDATA_PATH = os.path.join(ROOT_PATH, "UserData")

IMPORT_DATA_PATH = os.path.join(USERDATA_PATH, "Import")
