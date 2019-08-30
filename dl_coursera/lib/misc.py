import os


def format_dict(d):
    return ', '.join(['%s=%s' % (k, v) for k, v in d.items()])


def change_ext(filename, ext):
    return os.path.splitext(filename)[0] + ('' if ext == '' else '.' + ext)


def url_basename(url, *, _d={}):
    import re
    from urllib.parse import urlparse

    if _d.get('pat') is None:
        _d['pat'] = re.compile(r'([^/]*)$')

    match = _d['pat'].search(urlparse(url).path)
    return match.group(1)
