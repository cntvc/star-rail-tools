from star_rail.tui import HSRApp
from star_rail.utils.logger import logger


@logger.catch()
def run():
    app = HSRApp()
    app.run()


if __name__ == "__main__":
    run()
