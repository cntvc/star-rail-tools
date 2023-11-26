from .account import *
from .month import *
from .record import *
from .updater import Updater

account_manager = AccountClient


class HSRClient(GachaRecordClient, MonthInfoClient, AccountClient):
    pass


__all__ = ["HSRClient", "Updater"]
