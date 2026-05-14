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
        report('err', f'({self._cur_path(ndtxt=False)}) {msg}')
        raise err_sdialog_syntax(msg)

    def _warn(self, msg):
        report('war', f'({self._cur_path(ndtxt=False)}) {msg}')

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

    def _cur_path(self, bsback = 0, ndtxt = True, strict = True):
        cpath = []
        bsdst = len(self.blkstack) - 1 - bsback
        lst_para_idx = 0
        reached = False
        for bsidx, bsi in enumerate(self.blkstack):
            (btyp, *_), bname, para_idx, lflags = bsi
            cpath.append(bname.format(lst_para_idx + 1))
            lst_para_idx = para_idx
            if bsidx >= bsdst:
                reached = True
            if reached:
                if not ndtxt:
                    break
                elif self._getlflag('has_text', lflags):
                    break
                elif strict:
                    self._error('cur path without text')
        else:
            if reached:
                return None
            else:
                raise err_sdialog_syntax('cur path unreachable')
        if cpath:
            cpath.append(str(lst_para_idx + 1))
        else:
            cpath.append('ret')
        return  '/'.join(cpath)

    def _blk_step(self, step, half = False):
        if not self.blkstack:
            return
        binfo, bname, para_idx, lflags = self.blkstack.pop()
        if half:
            stpv = 1
        else:
            stpv = 2
            if step:
                para_idx += 1
        self.blkstack.append((binfo, bname, para_idx, {}))
        if self._getanylflag(('has_content', 'has_content_prv'), lflags):
            self._setlflag('has_content_prv', True)
        self._npath_blk_step(lflags, stpv)

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
            self._write_para_out(self._getblk(0)[0][0])
        self._blk_step(self._getlflag('has_content'))
        self.blkstack.append((binfo, bname, 0, {}))
        self._npath_blk_in(btyp)

    def _blk_out(self, with_el):
        if not self.blkstack:
            self._error('unbalance block')
        (btyp, *_), bname, _, lflags = self._getblk(0)
        has_text = self._getlflag('has_text', lflags)
        has_content = self._getanylflag(
            ('has_content', 'has_content_prv'), lflags)
        if has_content:
            if has_text:
                self._write_para_out(btyp)
        if btyp == 'func':
            self._npath_flush()
            if has_content:
                self._write_func_out(bname)
        self._npath_blk_out(btyp)
        self.blkstack.pop()
        self._blk_step(has_content, with_el)

    def _txt_in(self):
        assert self.blkstack
        (btyp, *_), bname, _, lflags = self._getblk(0)
        if self._getlflag('has_text', lflags):
            return
        for bsi in self.blkstack:
            (sbtyp, *_), sbname, _, slflags = bsi
            if self._getanylflag(('has_content', 'has_content_prv'), slflags):
                continue
            self._setlflag('has_content', True, slflags)
            if sbtyp == 'func':
                self._write_func_in(sbname)
        self._setlflag('has_content', True, lflags)
        self._setlflag('has_text', True, lflags)
        self._npath_rslv()
        self._write_para_in(btyp)

    def _getlpblkidx(self):
        for bsback, bsi in enumerate(reversed(self.blkstack)):
            if bsi[0][0] == 'lp':
                return bsback
        else:
            self._error('no loop')

    def _npath_gettab(self, lvars, new):
        if 'npath_req' in lvars:
            return lvars['npath_req']
        elif new:
            dft = lvars['npath_req'] = {}
            return dft
        else:
            return None

    def _npath_settab(self, lvars, tab):
        if tab is None:
            if 'npath_req' in lvars:
                lvars.pop('npath_req')
        else:
            if 'npath_req' in lvars:
                dtab = lvars['npath_req']
                for k, reqs in tab.items():
                    if k in dtab:
                        dtab[k].extend(reqs)
                    else:
                        dtab[k] = reqs
            else:
                lvars['npath_req'] = tab

    def _npath_req(self, hid, lvars):
        if lvars is None:
            reqs = self.gvars['npath_rcur']
        else:
            step = 2
            tab = self._npath_gettab(lvars, True)
            if step in tab:
                reqs = tab[step]
            else:
                reqs = tab[step] = []
        reqs.append(hid)
        rcnt = self.gvars['npath_rcnt'].get(hid, 0)
        self.gvars['npath_rcnt'][hid] = rcnt + 1

    def _npath_nxt(self):
        hid = self.hold(0)
        self._npath_req(hid, None)

    def _npath_bra(self, lvars):
        creqs = self.gvars['npath_rcur']
        for hid in creqs:
            self._npath_req(hid, lvars)

    def _npath_blk_step(self, lvars, step):
        stab = self._npath_gettab(lvars, False)
        if stab is None:
            return
        dblk = self._getblk(0)
        assert not dblk is None
        if step == 0:
            self._npath_settab(dblk[3], stab)
            return
        creqs = self.gvars['npath_rcur']
        dtab = {}
        for si in range(2, -1, -1):
            sreqs = stab.get(si, None)
            if not sreqs:
                continue
            di = si - step
            if di > 0:
                dtab[di] = sreqs
            else:
                creqs.extend(sreqs)
        if dtab:
            self._npath_settab(dblk[3], dtab)

    def _npath_blk_in(self, btyp):
        if btyp != 'lp' and btyp != 'if':
            return
        sblk = self._getblk(1)
        if sblk is None:
            return
        self._npath_bra(sblk[3])

    def _npath_reput(self, rinfo, cpath, wkset):
        hid = rinfo
        rcnt = self.gvars['npath_rcnt'].get(hid, 0)
        assert rcnt > 0
        if not hid in wkset:
            wkset.add(hid)
            if not cpath is None:
                self.reput(hid, (f'[next: {cpath}]',), True, True)
        if rcnt - 1 > 0:
            self.gvars['npath_rcnt'][hid] = rcnt - 1
        else:
            self.reput(hid, None, True, False)
            self.gvars['npath_rcnt'].pop(hid)

    def _npath_blk_out(self, btyp):
        creqs = self.gvars['npath_rcur']
        sblk = self._getblk(0)
        assert not sblk is None
        stab = self._npath_gettab(sblk[3], False)
        if not stab is None:
            for si in range(2, -1, -1):
                sreqs = stab.get(si, None)
                if not sreqs:
                    continue
                creqs.extend(sreqs)
        if len(creqs) == 0:
            return
        isback = False
        isbreak = False
        if self._getgflag('after_jump'):
            jtyp = self.gvars['jump_type']
            bbck = self._getlpblkidx()
            if jtyp == 'continue':
                isback = True
            elif jtyp == 'break':
                isbreak = True
            else:
                self._error(f'unknown jump type: {jtyp}')
        else:
            bbck = 0
            if btyp == 'lp':
                isback = True
        if not (isback or isbreak):
            return
        elif isback:
            npath = self._cur_path(bbck, strict = False)
            if npath is None:
                npath = 'no-text-loop: ' + self._cur_path(bbck, ndtxt = False)
            rpwks = set()
            for rinfo in creqs:
                self._npath_reput(rinfo, npath, rpwks)
        elif isbreak:
            dblk = self._getblk(bbck + 1)
            if dblk is None:
                return
            dtab = self._npath_gettab(dblk[3], True)
            if 2 in dtab:
                dreqs = dtab[2]
            else:
                dreqs = dtab[2] = []
            dreqs.extend(creqs)
        creqs.clear()

    def _npath_rslv(self):
        cpath = self._cur_path()
        creqs = self.gvars['npath_rcur']
        rpwks = set()
        for rinfo in creqs:
            self._npath_reput(rinfo, cpath, rpwks)
        creqs.clear()

    def _npath_flush(self):
        rpwks = set()
        for bsi in self.blkstack:
            tab = self._npath_gettab(bsi[3], False)
            if tab is None:
                continue
            for reqs in tab.values():
                for rinfo in reqs:
                    self._npath_reput(rinfo, 'ret', rpwks)
            self._npath_settab(bsi[3], None)
        creqs = self.gvars['npath_rcur']
        for rinfo in creqs:
            self._npath_reput(rinfo, 'ret', rpwks)
        creqs.clear()
        assert not self.gvars['npath_rcnt']

    def _write_func_in(self, bname):
        print('func', bname)
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
        self.flush()

    def _write_para_in(self, btyp):
        cpath = self._cur_path()
        if cpath.startswith('Scene-51cf0'):
            print('para_in', cpath)
            if cpath == 'Scene-51cf0/1-Pack/1-Pack/1-Pack/2-Then/1':
                #breakpoint()
                pass
        super().newline()
        super().write('-------------------')
        super().newline()
        super().write(f'[path: {cpath}]')
        super().newline()
        super().write('[text]')
        super().newline()

    def _write_para_out(self, btyp):
        super().write('[/text]')
        super().newline()
        self._npath_nxt()
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
            if ajchk:
                self._setgflag('after_jump', False)
                self.gvars.pop('jump_type')
                ajchk = False
        elif cmd == 'lpflow':
            self._setgflag('after_jump', True)
            self.gvars['jump_type'] = args[0]
        elif cmd == 'start':
            ename, = args
            if ename == 'prog':
                self.gvars['npath_rcnt'] = {}
                self.gvars['npath_rcur'] = []
        elif cmd == 'end':
            ename, = args
            if ename == 'prog':
                self.touch()
        else:
            if cmd == 'hold':
                super().meta(cmd, *args)
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
        if 1:
            cd = c_scode_program(ast, bind_sdialog_buf(c_scode_buf_null()))
            #cd = c_scode_program(ast, bind_sdialog_buf(c_scode_buf_std()))
            cd.gen_code()
        else:
            with open(r'wktab\dialog.txt', 'w', encoding = 'utf-8') as fd:
                cd = c_scode_program(ast, bind_sdialog_buf(c_scode_buf_fd(fd)))
                cd.gen_code()
    tst1()
