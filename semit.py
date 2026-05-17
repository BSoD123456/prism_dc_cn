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
                    self.fd.write()

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

@with_anode()
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

    def _reftab_reg(self, name, ctx):
        at = ctx['reftab_a']
        if name in at:
            self._error('duplicated ref name: {name}')
        addr = ctx['addr']
        at[name] = addr
        qt = ctx['reftab_q']
        if name in qt:
            for hid in qt.pop(name):
                pass

    def _reftab_req(self, name, ctx):
        at = ctx['reftab_a']
        if name in at:
            pass
            return
        qt = ctx['reftab_q']

    # program

    def _gen_anode_prog(self, nd, ctx):
        ctx = {}
        ctx['addr'] = 0
        ctx['reftab_a'] = {}
        ctx['reftab_q'] = {}
        buf = ctx['buf'] = self.buf
        buf.meta('start', 'prog')
        buf.meta('disline')
        buf.newline()
        for snd in nd.subs:
            self._gen_anode(snd, None, ctx)
            break
        buf.meta('end', 'prog')
        buf.meta('disline')
        buf.newline()

    def _gen_anode_label(self, nd, ctx):
        self._write_cmt(f'@lab.{nd.name}', ctx)

    def _gen_anode_func(self, nd, ctx):
        self._write_cmt(f'@fun.{nd.name}', ctx)
        self._gen_anode(nd.sub, None, ctx)

    def _gen_anode_parm(self, nd, ctx):
        self._write_cmt(f',arg{nd.aidx}', ctx)

    def _gen_anode_bat(self, nd, ctx):
        for snd in nd.subs:
            self._gen_anode(snd, None, ctx)

    def _gen_vnode_cmd(self, nd, ctx):
        cname = nd.name
        ccode = EM_CMD_INFO[cname]
        need_parm = False
        if len(ccode) > 1 and ccode[1] is None:
            need_parm = True
        for i, bnd in enumerate(nd.subs):
            snd = self._getone(bnd)
            if i == 0 and need_parm:
                ccode = (ccode[0], snd.val)
                continue
            self._gen_anode(snd, None, ctx)
        if need_parm:
            cdesc = f'{nd.name} ( 0x{0:x} )'
        else:
            cdesc = f'{nd.name}'
        self._write_cmd(cdesc, ccode, ctx)

    def _gen_anode_act(self, nd, ctx):
        self._gen_vnode_cmd(nd, ctx)

    def _gen_anode_act_return(self, nd, ctx):
        cname = nd.name
        self._write_cmd(cname, EM_CMD_INFO[cname], ctx)

    def _gen_anode_act_call(self, nd, ctx):
        self._gen_vnode_cmd(nd, ctx)

    def _gen_anode_act_setrval(self, nd, ctx):
        sub = self._getone(nd.subs[1])
        self._gen_anode(sub, None, ctx)

    def _gen_anode_ref_func(self, nd, ctx):
        buf = ctx['buf']
        buf.write(str(nd))
        buf.newline()

    def _gen_anode_ref_label(self, nd, ctx):
        buf = ctx['buf']
        buf.write(str(nd))
        buf.newline()

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
        if 1:
            #cd = c_semit_program(ast, c_scode_buf_null())
            cd = c_semit_program(ast, c_scode_buf_std())
            cd.gen_code()
        else:
            with open(r'wktab\escript.bin', 'wb') as fd:
                cd = c_semit_program(ast, c_semit_asm_buf_fd(fd))
                cd.gen_code()
    tst1()
