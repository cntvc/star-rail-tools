import atexit

from star_rail.tui import HSRApp
from star_rail.utils.logger import logger


@atexit.register
def on_exit():
    logger.complete()


@logger.catch()
def run():
    app = HSRApp()
    app.run()


if __name__ == "__main__":
    run()
