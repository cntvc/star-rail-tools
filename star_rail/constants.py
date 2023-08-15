import os
import sys

APP_NAME = "StarRailTools"

####################################################################
# path
####################################################################

ROOT_PATH = os.path.join(os.path.dirname(sys.argv[0]), APP_NAME)

APPDATA_PATH = os.path.join(ROOT_PATH, "AppData")
"""保存软件运行数据的根目录"""

TEMP_PATH = os.path.join(APPDATA_PATH, "temp")

CONFIG_PATH = os.path.join(APPDATA_PATH, "config")

LOG_PATH = os.path.join(APPDATA_PATH, "log")

DATA_PATH = os.path.join(APPDATA_PATH, "data")

IMPORT_DATA_PATH = os.path.join(ROOT_PATH, "import")

####################################################################
# constants
####################################################################

REQUEST_TIMEOUT = 3

MENU_BANNER_LENGTH = 40

####################################################################
# init
####################################################################

for path_var in [name for name in dir() if name.endswith("_PATH")]:
    path = globals()[path_var]
    os.makedirs(path, exist_ok=True)
