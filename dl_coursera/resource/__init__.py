import pkgutil


def load_resource(path):
    return pkgutil.get_data(__package__, path)
