#! python3
# coding: utf-8

from script import SC_CMD_INFO, SC_SYS_FUNC
from scode import with_anode, c_scode_parser, c_scode_buf_fd
from report import report

def _prs_cmd_info(cmd_list):
        rinfo = {}
        for ci, (nm, sb, *_) in enumerate(cmd_list):
            if isinstance(sb, int):
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

EM_SYS_FUNC = {}

class c_semit_asm_tok:

    def __init__(self, s, v):
        self.str = s
        self.val = v

    def __str__(self):
        return self.str

class c_semit_asm_buf_fd(c_scode_buf_fd):
    pass

@with_anode()
class c_semit_program(c_scode_parser):

    def __init__(self, ast, buf, conf = None):
        dconf = {}
        if conf:
            dconf = {**dconf, **conf}
        super().__init__(ast, buf, dconf)

    # program

    def _gen_anode_prog(self, nd, ctx):
        ctx = {}
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

    def _gen_anode_func(self, nd, ctx):
        buf = ctx['buf']
        buf.write(f'fun.{nd.name}')
        buf.newline()
        self._gen_anode(nd.sub, None, ctx)

    def _gen_anode_bat(self, nd, ctx):
        buf = ctx['buf']
        buf.write(c_semit_asm_tok('bat', 1))
        buf.newline()
        for snd in nd.subs:
            self._gen_anode(snd, None, ctx)

    def _gen_anode_act(self, nd, ctx):
        buf = ctx['buf']
        buf.write(f'act.{nd.name}')
        buf.newline()
        for bnd in nd.subs:
            self._gen_anode(bnd, None, ctx)

    def _gen_anode_act_call(self, nd, ctx):
        buf = ctx['buf']
        buf.write(f'call')
        buf.newline()
        for bnd in nd.subs:
            self._gen_anode(bnd, None, ctx)

    def _gen_anode_ref_func(self, nd, ctx):
        buf = ctx['buf']
        buf.write(str(nd))
        buf.newline()

    def _gen_anode_ref_label(self, nd, ctx):
        buf = ctx['buf']
        buf.write(str(nd))
        buf.newline()

    def _gen_anode_parm(self, nd, ctx):
        buf = ctx['buf']
        buf.write(str(nd))
        buf.newline()

    def _gen_anode_inst(self, nd, ctx, *, calc_value = None, **ka):
        buf = ctx['buf']
        val = nd.val
        if val & 0x4000000:
            val -= 0x8000000
        if calc_value:
            calc_value[0] = val
        buf.write(hex(val))
        buf.newline()

    def _gen_anode_label(self, nd, ctx):
        pass

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
