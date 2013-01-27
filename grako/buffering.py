# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
# FIXME: There could be a file buffer using random access
import re as regexp
from bisect import bisect as bisect
from collections import namedtuple

__all__ = ['Buffer']

RETYPutfE = type(regexp.compile('.'))

PosLine = namedtuple('PosLine', ['pos', 'line'])
LineInfo = namedtuple('LineInfo', ['line', 'col', 'start', 'text'])

class Buffer(object):
    def __init__(self, text,
                 filename='unknown',
                 whitespace=None,
                 ignorecase=False,
                 trace=False,
                 nameguard=True):
        self.original_text = text
        self.text = text
        self.filename = filename
        self.whitespace = set(whitespace if whitespace else ' \t\n\r\f\v')
        self.ignorecase = ignorecase
        self.trace = trace
        self.nameguard = nameguard
        self._fileinfo = self.get_fileinfo(text, filename)
        self._linecache = []
        self._preprocess()
        self._build_line_cache()
        self._pos = 0
        self._len = len(self.text)

    def _preprocess(self):
        pass

    @property
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, p):
        self.goto(p)

    @property
    def line(self):
        n = bisect(self._linecache, PosLine(self._pos, 0))
        return self._linecache[n - 1][1]

    @property
    def col(self):
        n = bisect(self._linecache, PosLine(self._pos, 0))
        start = self._linecache[n - 1][0]
        return self._pos - start - 1

    def atend(self):
        return self._pos >= self._len

    def ateol(self):
        return self.atend() or self.current() in '\r\n'

    def current(self):
        if self._pos >= self._len:
            return None
        return self.text[self._pos]

    def lookahead(self):
        if self.atend():
            return ''
        txt = (self.text[self.pos:self.pos + 80].split('\n')[0]).encode('unicode-escape')
        return '<%d:%d>%s' % (self.line + 1, self.col + 1, txt)

    def next(self):
        if self._pos >= self._len:
            return None
        c = self.text[self._pos]
        self._pos += 1
        return c

    def goto(self, p):
        self._pos = max(0, min(len(self.text), p))

    def move(self, n):
        self.goto(self.pos + n)

    def eatwhitespace(self):
        p = self._pos
        le = self._len
        ws = self.whitespace
        while p < le and self.text[p] in ws:
            p += 1
        self._pos = p

    def skip_to(self, c):
        p = self._pos
        le = self._len
        while p < le and self.text[p] != c:
            p += 1
        self._pos = p

    def skip_past(self, c):
        self.skip_to(c)
        self.next()

    def skip_to_eol(self):
        self.skip_to('\n')

    def is_space(self):
        return self.current() in self.whitespace

    def match(self, token, ignorecase=None):
        ignorecase = ignorecase if ignorecase is not None else self.ignorecase

        if token is None:
            return self.atend()

        p = self.pos
        if ignorecase:
            result = self.text[p:p + len(token)].lower() == token.lower()
        else:
            result = self.text[p:p + len(token)] == token

        if result:
            self.move(len(token))
            check_nameguard = not (self.nameguard and token.isalnum() and self.current().isalnum())
            if check_nameguard:
                return token
        self.goto(p)

    def matchre(self, pattern, ignorecase=None):
        ignorecase = ignorecase if ignorecase is not None else self.ignorecase
        if isinstance(pattern, RETYPE):
            re = pattern
        else:
            re = regexp.compile(pattern, regexp.IGNORECASE if ignorecase else 0)
        matched = re.match(self.text, self.pos)
        if matched:
            token = matched.group()
            self.move(len(token))
            return token

    def get_fileinfo(self, text, filename):
        return [filename] * len(text.splitlines())

    def _build_line_cache(self):
        cache = [PosLine(-1, 0)]
        n = 0
        for i, c in enumerate(self.text):
            if c == '\n':
                n += 1
                cache.append(PosLine(i , n))
        cache.append(PosLine(len(self.text), n + 1))
        self._linecache = cache

    def line_info(self, pos=None):
        if pos is None:
            pos = self.pos
        n = bisect(self._linecache, PosLine(pos, 0))
        start, line = self._linecache[n - 1]
        col = pos - start - 1
        text = self.text[start:self._linecache[n].pos]
        return LineInfo(line, col, start, text)

    def get_line(self, n=None):
        if n is None:
            n = self.line
        start, line = self._linecache[n][:2]
        assert line == n
        end, _ = self._linecache[n + 1]
        return self.text[start + 1:end]
