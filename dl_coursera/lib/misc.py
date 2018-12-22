import os


def format_dict(d):
    return ', '.join(['%s=%s' % (k, v) for k, v in d.items()])


def change_ext(filename, ext):
    return os.path.splitext(filename)[0] + ('' if ext == '' else '.' + ext)
