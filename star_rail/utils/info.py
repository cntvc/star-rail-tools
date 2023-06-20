import locale


def get_default_locale():
    return locale.getdefaultlocale()[0].lower()
