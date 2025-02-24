from loguru import logger

from star_rail.tui import HSRApp


@logger.catch()
def main():
    HSRApp().run()


if __name__ == "__main__":
    main()
