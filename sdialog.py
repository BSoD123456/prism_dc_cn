#! python3
# coding: utf-8

from scode import c_scode_program, c_scode_buf
from report import report

import re

class err_sdialog_syntax(ValueError):
    pass

class c_sdialog_buf(c_scode_buf):

    def __init__(self, *na, **ka):
        super().__init__(*na, **ka)
        self.blkstack = []
        self.pthseq = []
        self.gvars = {}

    def _error(self, msg):
        report('err', f'({self._cur_path()}) {msg}')
        raise err_sdialog_syntax(msg)

    def _warn(self, msg):
        report('war', f'({self._cur_path()}) {msg}')

    def _getgflag(self, key):
        return self.gvars.get(key, False)

    def _setgflag(self, key, val):
        self.gvars[key] = not not val

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
            (btyp, *_), bname, para_idx, _ = bsi
            if btyp == 'prog':
                continue
            cpath.append(bname.format(lst_para_idx + 1))
            lst_para_idx = para_idx
        if cpath:
            if nxt:
                cpath.append(str(lst_para_idx + 2))
            else:
                cpath.append(str(lst_para_idx + 1))
        else:
            cpath.append('ret')
        return  '/'.join(cpath)

    def _brk_path(self):
        cpath = []
        tpath = []
        lst_para_idx = 0
        lst_cpara_idx = 0
        for bsi in self.blkstack:
            (btyp, *_), bname, para_idx, _ = bsi
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
            (btyp, *_), bname, para_idx, _ = bsi
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

    def _blk_step(self, step, half):
        if not self.blkstack:
            return
        binfo, bname, para_idx, lflags = self.blkstack.pop()
        if step:
            if half:
                stpv = 1
            else:
                stpv = 2
                para_idx += 1
        else:
            stpv = 0
        nlflags = {}
        self.blkstack.append((binfo, bname, para_idx, nlflags))
        if self._getanylflag(('has_content', 'has_content_prv'), lflags):
            self._setlflag('has_content_prv', True, nlflags)
        self._npath_blk_step(lflags, nlflags, stpv)

    def _blk_in(self, binfo):
        btyp, *bargs = binfo
        if btyp == 'prog':
            bname = 'Prog'
        elif btyp == 'func':
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
            (pbtyp, *_), _, _, plflags = self._getblk(0)
            self._write_para_out(pbtyp, plflags)
        self._blk_step(self._getlflag('has_content'), btyp == 'el')
        self.blkstack.append((binfo, bname, 0, {}))

    def _blk_out(self, with_el):
        if not self.blkstack:
            self._error('unbalance block')
        (btyp, *_), bname, _, lflags = self.blkstack.pop()
        has_text = self._getlflag('has_text', lflags)
        has_content = self._getanylflag(
            ('has_content', 'has_content_prv'), lflags)
        if has_content:
            if has_text:
                self._write_para_out(btyp, lflags)
            if btyp == 'func':
                self._write_func_out(bname)
        nblk = self._getblk(0)
        if nblk:
            self._npath_blk_out(lflags, nblk[3])
        self._blk_step(has_content, with_el)

    def _txt_in(self):
        assert self.blkstack
        (btyp, *_), bname, _, lflags = self._getblk(0)
        if self._getlflag('has_text', lflags):
            return
        self._npath_rslv()
        for bsi in self.blkstack:
            (sbtyp, *_), sbname, _, slflags = bsi
            if self._getanylflag(('has_content', 'has_content_prv'), slflags):
                continue
            self._setlflag('has_content', True, slflags)
            if sbtyp == 'func':
                self._write_func_in(sbname)
        self._setlflag('has_content', True, lflags)
        self._setlflag('has_text', True, lflags)
        self._write_para_in(btyp)

    def _defer_para_out(self, btyp, bname, pout, fout):
        odinfo = self.gvars.get('defer_pout', None)
        if not odinfo is None:
            _, _, opout, ofout, _ = odinfo
            pout = (pout or opout)
            fout = (fout or ofout)
        if self._getgflag('after_jump') and btyp != 'lp':
            cpath = self._brk_path()
        else:
            cpath = self._cur_path(True)
        self.gvars['defer_pout'] = (btyp, bname, pout, fout, cpath)

    def _emit_para_out(self):
        dinfo = self.gvars.get('defer_pout', None)
        if dinfo is None:
            return
        btyp, bname, pout, fout, cpath = dinfo
        if pout:
            self._write_para_out(btyp, cpath)
        if fout:
            self._write_func_out(bname)
        self.gvars['defer_pout'] = None

    @staticmethod
    def _cmp_path(p1, p2):
        p1s = p1.split('/')
        p2s = p2.split('/')
        p1len = len(p1s)
        p2len = len(p2s)
        plen = min(p1len, p2len)
        assert plen > 0
        rcmp = 0
        for i in range(plen):
            k1 = p1s[i]
            k2 = p2s[i]
            if i == 0:
                assert k1 == k2
                continue
            v1 = int(k1.split('-')[0])
            v2 = int(k2.split('-')[0])
            if v1 > v2:
                rcmp = -1
            elif v1 < v2:
                rcmp = 1
            else:
                continue
            break
        return rcmp, i + 1 < p1len

    def _feed_path(self, path, fmt):
        super().write(fmt.format(path))
        super().newline()

    def _need_path(self, path, fmt):
        super().write(fmt.format(path))
        super().newline()

    def _flush_path(self):
        pass

    def _npath_gettab(self, lvars, new):
        if 'req_path' in lvars:
            return lvars['npath_req']
        elif new:
            dft = lvars['npath_req'] = {}
            return dft
        else:
            return None

    def _npath_newtab(self, lvars, tab):
        assert not 'req_path' in lvars
        lvars['npath_req'] = tab

    def _npath_req(self, lvars, step):
        tab = self._npath_gettab(lvars, True)
        if not step in tab:
            tab[step] = []
        hid = self.hold(None)
        tab[step].append(hid)

    def _npath_blk_step(self, slvars, dlvars, step):
        stab = self._npath_gettab(slvars, False)
        if stab is None:
            return
        if step == 0:
            self._npath_newtab(dlvars, stab)
            return
        dtab = {}
        for si in range(2, 0, -1):
            sreqs = stab.get(si, None)
            if not sreqs:
                continue
            di = si - step
            if di > 0:
                dtab[di] = sreqs
            else:
                if di in dtab:
                    dreqs = dtab[di]
                else:
                    dreqs = dtab[di] = {}
                dreqs.extend(sreqs)
        self._npath_newtab(dlvars, dtab)

    def _npath_blk_out(self, slvars, dlvars):
        stab = self._npath_gettab(slvars, False)
        if stab is None:
            return
        self._npath_newtab(dlvars, stab)

    def _npath_rslv(self):
        cpath = self._cur_path()
        for bsi in self.blkstack:
            tab = self._npath_gettab(bsi[3], False)
            if tab is None or not 0 in tab:
                continue
            for hid in tab.pop(0):
                self.reput(hid, cpath, True)

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
        self._flush_path()
        self.flush()

    def _write_para_in(self, btyp):
        cpath = self._cur_path()
        super().newline()
        super().write('-------------------')
        super().newline()
        self._feed_path(cpath, '[path: {}]')
        super().write('[text]')
        super().newline()

    def _write_para_out(self, btyp, lvars):
        super().write('[/text]')
        super().newline()
        super().write('[next: ')
        self._npath_req(lvars, 0)
        super().write(']')
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
            self._setgflag('after_jump', True)
        elif cmd == 'start':
            ename, = args
            if ename == 'prog':
                self._blk_in(args)
        elif cmd == 'end':
            ename, = args
            if ename == 'prog':
                self._blk_out(False)
                self.touch()
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

def bind_sdialog_buf(pbuf):
    return c_sdialog_buf(pbuf, False, 0)

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
    from scode import c_scode_buf_null, c_scode_buf_std, c_scode_buf_fd
    def tst1():
        global ast, cd
        ast = loadobj(r'wktab\ast.pck')
        print('start')
        if 0:
            cd = c_scode_program(ast, bind_sdialog_buf(c_scode_buf_null()))
            #cd = c_scode_program(ast, bind_sdialog_buf(c_scode_buf_std()))
            cd.gen_code()
        else:
            with open(r'wktab\dialog.txt', 'w', encoding = 'utf-8') as fd:
                cd = c_scode_program(ast, bind_sdialog_buf(c_scode_buf_fd(fd)))
                cd.gen_code()
    tst1()
