import logging
import copy

import bs4

import jinja2

from .resource import load_resource


def _is_root(e):
    return e.parent is None


def _is_tag(e):
    return isinstance(e, bs4.Tag)


def _has_no_child(tag):
    return len(tag.contents) == 0


class Traversal:
    '''depth-first traversal
    '''

    def __init__(self, root, *, tagOnly=False):
        assert _is_root(root)

        self._e = root
        self._skip_children = False
        self._tagOnly = tagOnly

    def __iter__(self):
        return self

    def __next__(self):
        e = self._next()
        if e is None:
            raise StopIteration('no more element')

        self._e = e
        self._skip_children = False
        return e

    def _next(self):
        if (not self._skip_children) and _is_tag(self._e):
            for e in self._e.children:
                if (not self._tagOnly) or _is_tag(e):
                    return e

        e = self._e
        while True:
            if _is_root(e):
                return None

            for _e in e.next_siblings:
                if (not self._tagOnly) or _is_tag(_e):
                    return _e

            e = e.parent

    def skip_children(self):
        self._skip_children = True


class CML:
    def __init__(self, doc):
        doc = doc.translate(doc.maketrans('\u21b5', ' '))
        self._root = bs4.BeautifulSoup(doc, 'lxml-xml')

        self._assetIDs = None
        self._html = None

    def get_assetIDs(self):
        if self._assetIDs is not None:
            return self._assetIDs

        self._assetIDs = []
        for e in Traversal(self._root, tagOnly=True):
            if e.name == 'asset':
                self._assetIDs.append(e['id'])
            elif e.name == 'img':
                self._assetIDs.append(e['assetId'])
        return self._assetIDs

    def to_html(self, *, assets):
        if self._html is not None:
            return self._html

        asset_by_id = {_['id']: _ for _ in assets}

        def _assetName(id_):
            return asset_by_id[id_]['name']

        html = bs4.BeautifulSoup('', 'lxml')
        d = {}

        def _add(e0, e1):
            parent1 = html
            _e = e0
            while _e is not None:
                if id(_e) in d:
                    parent1 = d[id(_e)]
                    break
                _e = _e.parent

            if (parent1 is html) and (not _is_tag(e0)):
                return

            if _is_tag(e0):
                d[id(e0)] = e1
            parent1.append(e1)

        tr = Traversal(self._root)
        for e0 in tr:
            if isinstance(e0, bs4.NavigableString):
                _li = str(e0).split('$$')
                hasMath = False
                for _ in _li:
                    if not hasMath:
                        _add(e0, _)
                    else:
                        _span = bs4.Tag(name='span')
                        _span['hasMath'] = 'true'
                        _span.append(_)
                        _add(e0, _span)

                    hasMath = not hasMath

                continue

            if not _is_tag(e0):
                continue

            if e0.name == 'asset':
                assert _has_no_child(e0)

                e1 = bs4.Tag(name='p')
                e1['class'] = 'asset'
                e1.append(_assetName(e0['id']))

            elif e0.name == 'img':
                assert _has_no_child(e0)

                e1 = bs4.Tag(name='img')
                e1['src'] = e1['alt'] = _assetName(e0['assetId'])

            elif e0.name == 'heading':
                e1 = bs4.Tag(name='h%d' % int(e0['level']))

            elif e0.name == 'text':
                e1 = bs4.Tag(name='p')

            elif e0.name == 'list':
                bulletType = e0['bulletType']
                if bulletType == 'numbers':
                    e1 = bs4.Tag(name='ol')
                    e1['type'] = '1'
                elif bulletType == 'bullets':
                    e1 = bs4.Tag(name='ul')
                else:
                    e1 = bs4.Tag(name='ul')
                    logging.warning('[CML] unknown bulletType=%s' % bulletType)

            elif e0.name == 'a':
                e1 = bs4.Tag(name='a')
                e1['href'] = e0['href']

            elif e0.name == 'code':
                e1 = bs4.Tag(name='pre')
                e1.append(copy.copy(e0))

                tr.skip_children()

            elif e0.name in ['li', 'strong', 'em', 'table', 'tr', 'td']:
                e1 = bs4.Tag(name=e0.name)

            else:
                continue

            _add(e0, e1)

        self._html = str(html)
        return self._html


def render_supplement(*, content, resource_path, title='', __={}):
    if __.get('template') is None:
        __['template'] = jinja2.Template(load_resource('template/supplement.html').decode('UTF-8'))
    return __['template'].render(content=content, resource_path=resource_path, title=title)
