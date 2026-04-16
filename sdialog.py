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

    def _error(self, msg):
        report('err', f'({self._cur_path()}) {msg}')
        raise err_sdialog_syntax(msg)

    def _warn(self, msg):
        report('war', f'({self._cur_path()}) {msg}')

    def _getgflag(self, key):
        return self.gflags.get(key, False)

    def _setgflag(self, key, val):
        self.gflags[key] = not not val

    def _getblk(self, idx):
        if len(self.blkstack) > idx:
            return self.blkstack[-idx-1]
        else:
            return None

    def _getlflag(self, key, lflags = None):
        if lflags is None:
            blk = self._getblk(0)
            if blk is None:
                return False
            lflags = blk[3]
        return lflags.get(key, False)

    def _setlflag(self, key, val, lflags = None):
        if lflags is None:
            blk = self._getblk(0)
            if blk is None:
                self._error('empty block stack')
            lflags = blk[3]
        lflags[key] = not not val

    def _getanylflag(self, keys, lflags = None):
        for key in keys:
            if self._getlflag(key, lflags):
                return True
        return False

    def _cur_path(self, nxt = False):
        cpath = []
        lst_para_idx = 0
        for bsi in self.blkstack:
            (btyp, *_), bname, para_idx, lflags = bsi
            cpath.append(bname.format(lst_para_idx + 1))
            lst_para_idx = para_idx
        if nxt:
            cpath.append(str(lst_para_idx + 2))
        else:
            cpath.append(str(lst_para_idx + 1))
        return  '/'.join(cpath)

    def _brk_path(self):
        cpath = []
        tpath = []
        lst_para_idx = 0
        lst_cpara_idx = 0
        for bsi in self.blkstack:
            (btyp, *_), bname, para_idx, lflags = bsi
            if btyp == 'lp':
                cpath.extend(tpath)
                lst_cpara_idx = lst_para_idx
                tpath = []
            tpath.append(bname.format(lst_para_idx + 1))
            lst_para_idx = para_idx
        if cpath:
            cpath.append(str(lst_cpara_idx + 2))
        else:
            cpath.append('ret')
        return  '/'.join(cpath)

    def _ctn_path(self):
        cpath = []
        tpath = []
        lst_para_idx = 0
        lst_cpara_idx = 0
        for bsi in self.blkstack:
            (btyp, *_), bname, para_idx, lflags = bsi
            tpath.append(bname.format(lst_para_idx + 1))
            lst_para_idx = para_idx
            if btyp == 'lp':
                cpath.extend(tpath)
                lst_cpara_idx = lst_para_idx
                tpath = []
        if cpath:
            cpath.append(str(lst_cpara_idx + 1))
        else:
            cpath.append('ret')
        return  '/'.join(cpath)

    def _blk_step(self, nostep = False):
        if not self.blkstack:
            return
        binfo, bname, para_idx, lflags = self.blkstack.pop()
        if not nostep:
            para_idx += 1
        self.blkstack.append((binfo, bname, para_idx, {}))
        if self._getanylflag(('has_content', 'has_content_prv'), lflags):
            self._setlflag('has_content_prv', True)

    def _blk_in(self, binfo):
        btyp, *bargs = binfo
        if btyp == 'func':
            bname = f'Scene-{bargs[0]}'
        elif btyp == 'lp':
            bname = '{}-Pack'
        elif btyp == 'if':
            bname = '{}-Then'
        elif btyp == 'el':
            bname = '{}-Else'
        else:
            self._error(f'unknown block: {btyp}')
        if self._getlflag('has_text'):
            self._write_para_out(self.blkstack[-1][0][0])
        self._blk_step(
            not self._getlflag('has_content')
            or btyp == 'el')
        self.blkstack.append((binfo, bname, 0, {}))

    def _txt_in(self):
        bs = self.blkstack
        assert len(bs) > 0
        (btyp, *_), bname, para_idx, lflags = self._getblk(0)
        if self._getlflag('has_text', lflags):
            return
        for bsi in bs:
            (sbtyp, *_), sbname, _, slflags = bsi
            if self._getanylflag(('has_content', 'has_content_prv'), slflags):
                continue
            self._setlflag('has_content', True, slflags)
            if sbtyp == 'func':
                self._write_func_in(sbname)
        self._setlflag('has_content', True, lflags)
        self._setlflag('has_text', True, lflags)
        self._write_para_in(btyp)

    def _blk_out(self, with_el):
        if not self.blkstack:
            self._error('unbalance block')
        (btyp, *_), bname, para_idx, lflags = self.blkstack.pop()
        if self._getlflag('has_text', lflags):
            self._write_para_out(btyp, self._getgflag('after_jump'))
        has_content = self._getanylflag(
            ('has_content', 'has_content_prv'), lflags)
        if has_content and btyp == 'func':
            self._write_func_out(bname)
        self._blk_step(not has_content or with_el)

    def _write_func_in(self, bname):
        cpath = self._cur_path()
        super().newline()
        super().write('====================')
        super().newline()
        super().write(f'[scene: {bname}]')
        super().newline()

    def _write_func_out(self, bname):
        super().write(f'[/scene: {bname}]')
        super().newline()
        super().write('====================')
        super().newline()
        super().newline()

    def _write_para_in(self, btyp):
        cpath = self._cur_path()
        super().newline()
        super().write('-------------------')
        super().newline()
        super().write(f'[path: {cpath}]')
        super().newline()
        super().write('[text]')
        super().newline()

    def _write_para_out(self, btyp, broken = False):
        if broken:
            cpath = self._brk_path()
        else:
            cpath = self._cur_path(True)
        super().write('[/text]')
        super().newline()
        super().write(f'[next: {cpath}]')
        super().newline()
        super().write('--------------------')
        super().newline()
        super().newline()

    def meta(self, cmd, *args):
        assert not self._getgflag('in_text') or cmd == 'text_done'
        ajchk = self._getgflag('after_jump')
        if cmd == 'text':
            self._txt_in()
            self._setgflag('in_text', True)
        elif cmd == 'text_done':
            assert self._getgflag('in_text')
            self._setgflag('in_text', False)
            self._setlflag('after_text', True)
        elif cmd == 'text_print':
            sfname, = args
            if not self._getlflag('after_text'):
                if self._getlflag('has_text'):
                    self._warn(f'print before text: {args[0]}')
            elif not self._getgflag('last_lf'):
                if sfname != 'set_name':
                    #self._warn(f'print without LF: {args[0]}')
                    super().newline()
            self._setlflag('after_text', False)
        elif cmd == 'block':
            if not args[0] == 'vo':
                self._blk_in(args)
        elif cmd == 'block_done':
            if not args[0] == 'vo':
                self._blk_out(len(args) > 1 and args[1] == 'el')
            self._setgflag('after_jump', False)
            ajchk = False
        elif cmd == 'lpflow':
            if self._getanylflag(('has_content', 'has_content_prv')):
                self._txt_in()
            self._setgflag('after_jump', True)
        else:
            ajchk = False
        if ajchk:
            self._error('something after jump')

    def _rplc_ctrl(self, txt):
        rtxt = re.sub(r'\[LF\]', '\n', txt)
        if rtxt and rtxt[-1] == '\n':
            self._setgflag('last_lf', True)
        else:
            self._setgflag('last_lf', False)
        return rtxt

    def write(self, s):
        if self._getgflag('in_text'):
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

c_sdialog_buf_null = make_sdialog_buf_class(c_scode_buf_null)
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
            cd = c_scode_program(ast, c_sdialog_buf_null())
            #cd = c_scode_program(ast, c_sdialog_buf_std())
            cd.gen_code()
        else:
            with open(r'wktab\dialog.txt', 'w', encoding = 'utf-8') as fd:
                cd = c_scode_program(ast, c_sdialog_buf_fd(fd))
                cd.gen_code()
    tst1()
