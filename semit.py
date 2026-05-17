#! python3
# coding: utf-8

from mark import val2bytes
from script import SC_CMD_INFO, SC_SYS_FUNC
from scode import with_anode, c_scode_parser, c_scode_buf_fd
from report import report

class c_semit_asm_tok:

    def __init__(self, s, v):
        self.desc = s
        self.code = v

    def bytes(self):
        cc = self.code
        if cc is None:
            return b''
        cv = cc[0] << 0x1b
        if len(cc) > 1:
            cv |= cc[1]
        return val2bytes(cv, 4)

    def text(self):
        if self.code:
            return self.desc.format(self.code[1:])
        else:
            return self.desc

    def __str__(self):
        bs = self.bytes()
        ds = self.text()
        if bs:
            cs = ' '.join(f'{b:02X}' for b in bs)
            return f'{cs}: {ds}'
        else:
            return ds

class c_semit_asm_buf_fd(c_scode_buf_fd):

    def _conltoks(self, ltoks):
        for tok in ltoks:
            if isinstance(tok, c_semit_asm_tok):
                bs = tok.bytes()
                if bs:
                    self.fd.write(bs)

    def _writeltoks(self, ltoks):
        self._mergeltoks(ltoks)

def _prs_cmd_info(cmd_list):
        rinfo = {}
        for ci, (nm, sb, *_) in enumerate(cmd_list):
            if isinstance(sb, int):
                if sb > 0:
                    assert sb == 1
                    rinfo[nm] = (ci, None)
                else:
                    rinfo[nm] = (ci,)
                continue
            elif isinstance(sb, dict):
                sbit = sb.items()
            else:
                sbit = enumerate(sb)
            for si, (snm, *_) in sbit:
                if si == '__par__':
                    assert snm is None
                    rinfo[nm] = (ci, None)
                    continue
                dnm = nm
                if not snm is None:
                    dnm = '_'.join((nm, snm))
                rinfo[dnm] = (ci, si)
        return rinfo
EM_CMD_INFO = _prs_cmd_info(SC_CMD_INFO)
EM_SYS_FUNC = {nm: si for si, (nm, *_) in enumerate(SC_SYS_FUNC)}

@with_anode('call', 'syscall', 'txtcall')
class c_semit_program(c_scode_parser):

    def __init__(self, ast, buf, conf = None):
        dconf = {}
        if conf:
            dconf = {**dconf, **conf}
        super().__init__(ast, buf, dconf)

    def _write_cmd(self, desc, code, ctx):
        ctx['buf'].write(c_semit_asm_tok(desc, code))
        ctx['buf'].newline()
        ctx['addr'] += 1

    def _write_cmt(self, desc, ctx):
        ctx['buf'].write(c_semit_asm_tok(desc, None))
        ctx['buf'].newline()

    def _inst_ccode(self, val):
        ccode = EM_CMD_INFO['push']
        assert ccode[1] is None
        return ccode[0], val

    def _reftab_reg(self, name, ctx):
        at = ctx['reftab_a']
        if name in at:
            self._error(None, f'duplicated ref name: {name}')
        addr = ctx['addr']
        at[name] = addr
        qt = ctx['reftab_q']
        if name in qt:
            tok = c_semit_asm_tok(f'&{name}', self._inst_ccode(at[name]))
            for hid in qt.pop(name):
                ctx['buf'].reput(hid, tok, True)

    def _reftab_req(self, name, ctx):
        at = ctx['reftab_a']
        if name in at:
            self._write_cmd(f'&{name}', self._inst_ccode(at[name]), ctx)
            return
        qt = ctx['reftab_q']
        if name in qt:
            reqs = qt[name]
        else:
            reqs = qt[name] = []
        hid = ctx['buf'].hold(0)
        reqs.append(hid)

    def _reftab_flush(self, ctx):
        qt = ctx['reftab_q']
        rq = [*qt.keys()]
        for name in rq:
            self._reftab_reg(name, ctx)
        return rq

    # program

    def _gen_anode_prog(self, nd, ctx):
        ctx = {}
        ctx['addr'] = 0
        ctx['reftab_a'] = {}
        ctx['reftab_q'] = {}
        buf = ctx['buf'] = self.buf.sub(0)
        buf.meta('start', 'prog')
        buf.meta('disline')
        buf.newline()
        for snd in nd.subs:
            self._gen_anode(snd, None, ctx)
            if not ctx['reftab_q']:
                buf.touch()
                buf = ctx['buf'] = self.buf.sub(0)
            #break
        buf.meta('end', 'prog')
        buf.meta('disline')
        buf.newline()
        rq = self._reftab_flush(ctx)
        buf.touch()
        if rq:
            if len(rq) > 5:
                rq = rq[:5]
                rq.append('...')
            rqs = ', '.join(rq)
            self._error(nd, f'reference undefined: {rqs}')

    # text

    def _gen_anode_text(self, nd, ctx):
        name = f'txt.{nd.name}'
        self._write_cmt('@' + name, ctx)
        self._reftab_reg(name, ctx)
        txt = nd.text
        tidx = 0
        cpair = []
        cphi = False
        def emit():
            v1 = cpair[0]
            v2 = cpair[1] if len(cpair) > 1 else 0x1fff
            cpair.clear()
            val = (((v2 & 0x1fff) << 0xd) | (v1 & 0x1fff))
            if cphi:
                cname = 'texth'
            else:
                cname = 'text'
            ccode = EM_CMD_INFO[cname]
            assert ccode[1] is None
            self._write_cmd(name, (ccode[0], val), ctx)
        while True:
            if tidx >= len(txt):
                if cpair:
                    emit()
                break
            c = txt[tidx]
            ishi = not not (c | 0x2000)
            c &= 0x1fff
            if cphi != ishi:
                if cpair:
                    emit()
                cphi = ishi
                continue
            cpair.append(c)
            tidx += 1
            if len(cpair) >= 2:
                emit()

    # struct

    def _gen_anode_label(self, nd, ctx):
        name = f'lab.{nd.name}'
        self._write_cmt('@' + name, ctx)
        self._reftab_reg(name, ctx)

    def _gen_anode_func(self, nd, ctx):
        name = f'fun.{nd.name}'
        self._write_cmt('@' + name, ctx)
        self._reftab_reg(name, ctx)
        self._gen_anode(nd.sub, None, ctx)

    def _gen_anode_parm(self, nd, ctx):
        self._write_cmt(f',arg{nd.aidx}', ctx)

    def _gen_anode_bat(self, nd, ctx):
        for snd in nd.subs:
            self._gen_anode(snd, None, ctx)

    # act

    def _gen_vnode_cmd(self, nd, ctx):
        cname = nd.name
        ccode = EM_CMD_INFO[cname]
        need_parm = False
        if len(ccode) > 1 and ccode[1] is None:
            parm = self._getone(nd.subs[0])
            ccode = (ccode[0], parm.val)
            cdesc = f'{cname} ( 0x{0:x} )'
            rmsubs = nd.subs[1:]
        else:
            cdesc = f'{cname}'
            rmsubs = nd.subs
        return cdesc, ccode, rmsubs

    def _gen_anode_act(self, nd, ctx):
        cdesc, ccode, rmsubs = self._gen_vnode_cmd(nd, ctx)
        for bnd in rmsubs:
            snd = self._getone(bnd)
            self._gen_anode(snd, None, ctx)
        self._write_cmd(cdesc, ccode, ctx)

    def _gen_anode_act_return(self, nd, ctx):
        cname = nd.name
        self._write_cmd(cname, EM_CMD_INFO[cname], ctx)

    def _gen_anode_act_call(self, nd, ctx):
        cdesc, ccode, rmsubs = self._gen_vnode_cmd(nd, ctx)
        for bnd in rmsubs:
            snd = self._getone(bnd)
            self._gen_any_anode(snd, ('call', None), ctx)
        self._write_cmd(cdesc, ccode, ctx)

    def _gen_anode_act_call_txtcall(self, nd, ctx):
        cdesc, ccode, rmsubs = self._gen_vnode_cmd(nd, ctx)
        for bnd in rmsubs:
            snd = self._getone(bnd)
            self._gen_any_anode(snd, ('txtcall', None), ctx)
        self._write_cmd(cdesc, ccode, ctx)

    def _gen_anode_act_call_syscall(self, nd, ctx):
        cdesc, ccode, rmsubs = self._gen_vnode_cmd(nd, ctx)
        for bnd in rmsubs:
            snd = self._getone(bnd)
            self._gen_any_anode(snd, ('syscall', None), ctx)
        self._write_cmd(cdesc, ccode, ctx)

    def _gen_anode_act_setrval(self, nd, ctx):
        sub = self._getone(nd.subs[1])
        self._gen_anode(sub, None, ctx)

    # ref

    def _gen_anode_ref_func__call(self, nd, ctx):
        self._reftab_req(f'fun.{nd.name}', ctx)

    def _gen_anode_ref_func__txtcall(self, nd, ctx):
        self._reftab_req(f'txt.{nd.name}', ctx)

    def _gen_anode_ref_func__syscall(self, nd, ctx):
        sname = nd.name
        scode = EM_SYS_FUNC[sname]
        self._write_cmd(f'&sys.{sname}', self._inst_ccode(scode), ctx)

    def _gen_anode_ref_label(self, nd, ctx):
        self._reftab_req(f'lab.{nd.name}', ctx)

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
    from scode import c_scode_buf_null, c_scode_buf_std
    def tst1():
        global ast, cd
        ast = loadobj(r'wktab\ast.pck')
        print('start')
        if 0:
            #cd = c_semit_program(ast, c_scode_buf_null())
            cd = c_semit_program(ast, c_scode_buf_std())
            cd.gen_code()
        else:
            with open(r'wktab\escript.bin', 'wb') as fd:
                cd = c_semit_program(ast, c_semit_asm_buf_fd(fd))
                cd.gen_code()
    tst1()
