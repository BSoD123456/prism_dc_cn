#! python3
# coding: utf-8

from scode import (
    c_scode_program, c_scode_buf_null, c_scode_buf_std, c_scode_buf_fd)
from report import report

class err_sdialog_syntax(ValueError):
    pass

class c_sdialog_buf_mixin:

    def __init__(self, *na, **ka):
        super().__init__(*na, **ka)
        self.blkstack = []
        self.intext = False

    def meta(self, cmd, *args):
        if cmd == 'text':
            assert not self.intext
            self.intext = True
        elif cmd == 'text_done':
            assert self.intext
            self.intext = False
        elif cmd == 'block':
            super().newline()
            super().write('====================')
            super().newline()
            super().write('--------------------')
            super().newline()
        elif cmd == 'block_done':
            super().newline()
            super().write('--------------------')
            super().newline()
            super().write('====================')
            super().newline()

    def write(self, s):
        if self.intext:
            super().write(s)

    def newline(self):
        super().meta('disline')
        super().newline()

def make_sdialog_buf_class(bcls):
    class c_sdialog_buf(c_sdialog_buf_mixin, bcls):
        pass
    bnms = bcls.__name__.split('_')
    try:
        bi = bnms.index('buf')
        c_sdialog_buf.__name__ = '_'.join((
            c_sdialog_buf.__name__, *bnms[bi+1:]))
    except:
        pass
    return c_sdialog_buf

c_sdialog_buf_std = make_sdialog_buf_class(c_scode_buf_std)
c_sdialog_buf_fd = make_sdialog_buf_class(c_scode_buf_fd)

if __name__ == '__main__':
    import pdb
    from hexdump import hexdump as hd
    from pprint import pprint
    ppr = lambda *a, **ka: pprint(*a, **ka, sort_dicts = False)

    import pickle
    def loadobj(n):
        with open(n, 'rb') as fd:
            return pickle.load(fd)

    from script import *
    def tst1():
        global ast, cd
        ast = loadobj(r'wktab\ast.pck')
        print('start')
        if 1:
            #cd = c_scode_program(ast, c_scode_buf_null())
            cd = c_scode_program(ast, c_sdialog_buf_std())
            cd.gen_code()
        else:
            with open(r'wktab\dialog.txt', 'w', encoding = 'utf-8') as fd:
                cd = c_scode_program(ast, c_sdialog_buf_fd(fd))
                cd.gen_code()
    tst1()
