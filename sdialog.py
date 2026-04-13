#! python3
# coding: utf-8

from scode import (
    c_scode_program, c_scode_buf_null, c_scode_buf_std, c_scode_buf_fd)
from report import report

import re

class err_sdialog_syntax(ValueError):
    pass

class c_sdialog_buf_mixin:

    def __init__(self, *na, **ka):
        super().__init__(*na, **ka)
        self.blkstack = []
        self.blkvdeep = 0
        self.intext = False

    def _cur_func_name(self):
        for i in range(self.blkvdeep-1, -1, -1):
            btyp, *bargs = self.blkstack[i]
            if btyp == 'func':
                return bargs[0]

    def _error(self, msg):
        report('err', f'({self._cur_func_name()}) {msg}')
        raise err_sdialog_syntax(msg)

    def _warn(self, msg):
        report('war', f'({self._cur_func_name()}) {msg}')

    def _blk_in(self, binfo):
        self.blkstack.append(binfo)

    def _txt_in(self):
        for i in range(self.blkvdeep, len(self.blkstack)):
            self._write_blk_in(*self.blkstack[i])
        self.blkvdeep = len(self.blkstack)

    def _blk_out(self):
        blen = len(self.blkstack)
        if blen < 1:
            self._error('unbalance block')
        binfo = self.blkstack.pop()
        if self.blkvdeep == blen:
            self._write_blk_out(*binfo)
        self.blkvdeep = min(self.blkvdeep, blen - 1)

    def _write_blk_in(self, btyp, *args):
        super().newline()
        if btyp == 'func':
            fname, = args
            super().write('====================')
            super().newline()
            super().write(f'Scene: {fname}')
            super().newline()
            super().write('--------------------')
        else:
            super().write(f'-------------------> b1')
        super().newline()

    def _write_blk_out(self, btyp, *args):
        if btyp == 'func':
            super().write('--------------------')
            super().newline()
            super().write('====================')
        else:
            super().write('f1 <--------------------')
        super().newline()
        super().newline()

    def meta(self, cmd, *args):
        if cmd == 'text':
            assert not self.intext
            self.intext = True
        elif cmd == 'text_done':
            assert self.intext
            self.intext = False
        elif cmd == 'text_print':
            assert not self.intext
            skptp = False
            if not self.blkvdeep == len(self.blkstack):
                self._warn(f'print before text: {args[0]}')
                skptp = True
            elif not (self.lbuf and self.lbuf[-1] == '\n'):
                self._warn(f'print without LF: {args[0]}')
                skptp = True
            if not skptp:
                super().newline()
        elif cmd == 'block':
            self._blk_in(args)
        elif cmd == 'block_done':
            self._blk_out()

    def _rplc_ctrl(self, txt):
        return re.sub(r'\[LF\]', '\n', txt)

    def write(self, s):
        if self.intext:
            self._txt_in()
            super().write(self._rplc_ctrl(s))

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
        if 0:
            #cd = c_scode_program(ast, c_scode_buf_null())
            cd = c_scode_program(ast, c_sdialog_buf_std())
            cd.gen_code()
        else:
            with open(r'wktab\dialog.txt', 'w', encoding = 'utf-8') as fd:
                cd = c_scode_program(ast, c_sdialog_buf_fd(fd))
                cd.gen_code()
    tst1()
