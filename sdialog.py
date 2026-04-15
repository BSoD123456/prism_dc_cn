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
        self.gflags = {}

    def _getflag(self, key):
        return self.gflags.get(key, False)

    def _setflag(self, key, val):
        self.gflags[key] = not not val

    def _cur_path(self):
        cpath = []
        lst_para_idx = 0
        for bsi in self.blkstack:
            (btyp, *_), bname, para_idx, has_content, has_text = bsi
            if has_content:
                cpath.append(bname.format(lst_para_idx))
                lst_para_idx = para_idx
        return '/'.join(cpath)

    def _error(self, msg):
        report('err', f'({self._cur_path()}) {msg}')
        raise err_sdialog_syntax(msg)

    def _warn(self, msg):
        report('war', f'({self._cur_path()}) {msg}')

    def _blk_in(self, binfo):
        btyp, *bargs = binfo
        has_text = False
        has_content = False
        if btyp == 'func':
            bname = f'Scene-{bargs[0]}'
            has_content = True
        elif btyp == 'lp':
            bname = 'Choose@{}'
        elif btyp == 'if':
            bname = 'Case@{}'
        elif btyp == 'el':
            bname = 'Case@{}B'
        else:
            self._error(f'unknown block: {btyp}')
        self.blkstack.append([
            binfo, bname, 0, has_content, has_text])

    def _txt_in(self):
        bs = self.blkstack
        assert len(bs) > 0
        for bsi in bs[:-1]:
            if bsi[0][0] == 'lp':
                bsi[3] = True
        bs[-1][3] = True
        bs[-1][4] = True
        self._write_blk_in(bs[-1][0][0], self._cur_path())

    def _blk_out(self):
        if not self.blkstack:
            self._error('unbalance block')
        (btyp, *_), bname, para_idx, has_content, has_text = self.blkstack.pop()
        if has_text:
            self._write_blk_out(btyp, bname)
            if self.blkstack:
                self.blkstack[-1][4] = True

    def _write_blk_in(self, btyp, *args):
        super().newline()
        if btyp == 'func':
            fname, = args
            super().write('====================')
            super().newline()
            super().write(f'[Scene: {fname}]')
            super().newline()
            super().write('--------------------')
            super().newline()
        else:
            super().write('-------------------')
            super().newline()
            super().write('[id: ?]')
            super().newline()
            if btyp == 'if':
                super().write('[goto: ?]')
                super().newline()
        super().write('[text]')
        super().newline()

    def _write_blk_out(self, btyp, bname):
        super().write('[/text]')
        super().newline()
        if btyp == 'func':
            super().write('--------------------')
            super().newline()
            super().write(f'[/Scene: {bname}]')
            super().newline()
            super().write('====================')
        else:
            super().write('--------------------')
        super().newline()
        super().newline()

    def meta(self, cmd, *args):
        assert not self._getflag('intext') or cmd == 'text_done'
        if cmd == 'text':
            self._txt_in()
            self._setflag('intext', True)
        elif cmd == 'text_done':
            assert self._getflag('intext')
            self._setflag('intext', False)
        elif cmd == 'text_print':
            sfname, = args
            if not self.blkstack[-1][4]:
                self._warn(f'print before text: {args[0]}')
            elif not self._getflag('lastlf'):
                if sfname != 'set_name':
                    #self._warn(f'print without LF: {args[0]}')
                    super().newline()
        elif cmd == 'block':
            if not args[0] == 'vo':
                self._blk_in(args)
        elif cmd == 'block_done':
            self._setflag('afterjump', False)
            if not args[0] == 'vo':
                self._blk_out()
        elif cmd == 'lpflow':
            self._setflag('afterjump', True)

    def _rplc_ctrl(self, txt):
        rtxt = re.sub(r'\[LF\]', '\n', txt)
        if rtxt and rtxt[-1] == '\n':
            self._setflag('lastlf', True)
        else:
            self._setflag('lastlf', False)
        return rtxt

    def write(self, s):
        if self._getflag('intext'):
            if self._getflag('afterjump'):
                self._error('texts should not after jump')
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
