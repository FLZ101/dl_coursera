import collections


class _Path:
    def __init__(self, li, *, absolute):
        self.li = li
        self.absolute = absolute

        if self.absolute:
            assert len(self.li) > 0 and self.li[0].isRoot()

    def __str__(self):
        if len(self.li) < 2:
            res = ''
        else:
            res = []
            for _1, _2 in zip(self.li[:-1], self.li[1:]):
                assert _1.parent is _2 or _2.parent is _1
                res.append('..' if _1.parent is _2 else _2.name)
            res = '/'.join(res)

        if self.absolute:
            res = '/' + res
        if res == '':
            res = '.'
        return res


class _Node:
    def __init__(self, name):
        self.name = name
        self.parent = None
        self.children = []

    def isRoot(self):
        return self.parent is None

    def _abspath(self):
        li = []
        node = self
        while node is not None:
            li.insert(0, node)
            node = node.parent
        return _Path(li, absolute=True)

    def _relpathTo(self, dst):
        li_self = self._abspath().li
        li_dst = dst._abspath().li

        i = -1
        for _1, _2 in zip(li_self, li_dst):
            if _1 is not _2:
                break
            i += 1
        assert i >= 0  # because every abspath starts with the root node

        li = li_self[-1:i:-1] + li_dst[i:]
        return _Path(li, absolute=False)

    def _relpathFrom(self, src):
        return src._relpathTo(self)

    def abspath(self):
        return str(self._abspath())

    def relpathTo(self, dst):
        return str(self._relpathTo(dst))

    def relpathFrom(self, src):
        return str(self._relpathFrom(src))

    def _append(self, node):
        node.parent = self
        self.children.append(node)

    def __str__(self):
        return self.abspath()


class ExploringTree:
    def __init__(self):
        self._root = _Node('')
        self._whereami = self._root
        self._old_whereami_stack = []

    def whereami(self):
        return self._whereami

    def up(self):
        assert self._whereami is not self._root

        self._whereami = self._whereami.parent

    def down(self, name):
        assert name != ''

        d = {_.name: _ for _ in self._whereami.children}
        if name in d:
            self._whereami = d[name]
        else:
            node = _Node(name)
            self._whereami._append(node)
            self._whereami = node

    def jump(self, dst):
        if isinstance(dst, _Node):
            self._whereami = dst
            return dst
        assert isinstance(dst, str)

        if len(dst) == 0:
            return self._whereami

        li = dst.split('/')
        if li[0] == '':
            self._whereami = self._root
            li = li[1:]

        for name in li:
            if name == '.':
                continue
            elif name == '..':
                self.up()
            elif name == '':
                continue
            else:
                self.down(name)

        return self._whereami

    def see(self, dst):
        with self:
            return self.jump(dst)

    def abspath(self):
        return self._whereami.abspath()

    def relpathTo(self, dst):
        return self._whereami.relpathTo(dst)

    def relpathFrom(self, src):
        return self._whereami.relpathFrom(src)

    def __enter__(self):
        self._old_whereami_stack.append(self._whereami)

    def __exit__(self, exc_type, exc_value, traceback):
        self._whereami = self._old_whereami_stack.pop()
