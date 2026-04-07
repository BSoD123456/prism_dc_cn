#! python3
# coding: utf-8

from charset import c_charset_jp
from report import report

class err_scode_syntax(ValueError):
    pass

class c_scode_buf:

    IDTSYM = '    '

    def __init__(self, parent, touched, indent):
        self.par = parent
        self.tch = touched
        self.idt = indent
        self.lbuf = []
        self.buf = []

    def sub(self, idt = 1):
        return c_scode_buf(self, False, self.idt + idt)

    def indent(self, val):
        self.idt += val
        if self.idt < 0:
            raise err_scode_syntax('indent underflow')

    def popindent(self):
        idt = self.idt
        self.idt = self.par.idt if self.par else 0
        return idt - self.idt

    def _idtsym(self):
        return (self.IDTSYM for _ in range(self.idt))

    def _writeline(self, line):
        if self.tch:
            self.par._writeline(line)
        else:
            self.buf.append(line)

    def write(self, s):
        self.lbuf.append(s)

    def newline(self):
        if self.lbuf:
            line = ''.join((*self._idtsym(), *self.lbuf))
            self.lbuf = []
        else:
            line = ''
        self._writeline(line)

    def touch(self):
        if self.tch:
            return self
        self.tch = True
        for line in self.buf:
            self._writeline(line)
        return self

class c_scode_buf_null(c_scode_buf):

    def __init__(self):
        super().__init__(None, True, 0)

    def _writeline(self, line):
        pass

class c_scode_buf_std(c_scode_buf):

    def __init__(self):
        super().__init__(None, True, 0)

    def _writeline(self, line):
        print(line)

def with_anode(cls):
    nmset = set()
    for mn in dir(cls):
        if not mn.startswith('_gen_anode_'):
            continue
        nm = mn.split('__')[0]
        nmset.add(nm)
    def _dispatch_anode(self, nd, assume):
        ctype = nd.__class__.__name__
        assert ctype.startswith('c_script_anode_')
        nm = '_gen_anode_' + ctype[len('c_script_anode_'):]
        if hasattr(nd, 'name'):
            nm2 = '_'.join((nm, nd.name))
            if nm2 in nmset:
                nm = nm2
        if assume:
            nm = '__'.join((nm, assume))
        return getattr(self, nm, None), nm[len('_gen_anode_'):]
    cls._dispatch_anode = _dispatch_anode
    return cls

@with_anode
class c_scode_program:

    def __init__(self, ast, buf):
        self.ast = ast
        self.buf = buf
        self.chrset = c_charset_jp()

    def _error(self, nd, msg):
        addr = getattr(nd, 'addr', -1)
        report('err', f'(addr:{addr:x}) {msg}')
        raise err_scode_syntax(msg)

    def _warn(self, nd, msg):
        addr = getattr(nd, 'addr', -1)
        report('war', f'(addr:{addr:x}) {msg}')

    def _getone(self, nd):
        if len(nd.subs) != 1:
            self._error(nd, f'anode should have only 1 subnode: {nd}')
        return nd.subs[0]

    def _gen_anode(self, nd, assume = None, ctx = None):
        mth, mn = self._dispatch_anode(nd, assume)
        if not mth:
            self._error(nd, f'should not be assumed as: {mn}')
        mth(nd, ctx)
        return mn

    # program

    def _gen_anode_prog(self, nd, ctx):
        print('start')
        ctx = {}
        ctx['buf'] = c_scode_buf_null()
        ctx['text'] = {}
        for snd in nd.subs:
            self._gen_anode(snd, 'dectext', ctx)
        buf = ctx['buf'] = self.buf
        for snd in nd.subs:
            if self._gen_anode(snd, None, ctx) == 'func':
                buf.newline()

    # struct

    def _gen_anode_func__dectext(self, nd, ctx):
        pass

    def _gen_anode_text__dectext(self, nd, ctx):
        if nd.name in ctx['text']:
            self._error(nd, f'duplicated text name: {nd.name}')
        txts = []
        for c in nd.text:
            txts.append(self.chrset.dec(c))
        txt = ''.join(txts)
        ctx['text'][nd.name] = txt
        ctx['buf'].write(f'txt.{nd.name} = "{txt}";')
        ctx['buf'].newline()

    def _gen_anode_func(self, nd, ctx):
        pbuf = ctx['buf']
        if nd.rnum == 1:
            rr = 'ret '
        else:
            rr = ', '.join(f'ret{i+1}' for i in range(nd.rnum))
            if nd.rnum > 1:
                rr = rr + ' '
        ar = ', '.join(f'arg{i+1}' for i in range(nd.anum))
        pbuf.write(f'{rr}fun.{nd.name}({ar}) {{')
        pbuf.newline()
        buf = ctx['buf'] = pbuf.sub()
        self._gen_anode(nd.sub, 'prim', ctx)
        buf.touch()
        ctx['buf'] = pbuf
        pbuf.write('}')
        pbuf.newline()

    def _gen_anode_text(self, nd, ctx):
        pass

    def _gen_anode_bat__prim(self, nd, ctx):
        for snd in nd.subs:
            self._gen_anode(snd, 'prim', ctx)

    def _gen_anode_bat__inret(self, nd, ctx):
        for i, snd in enumerate(nd.subs):
            if i == 0:
                self._gen_anode(snd, None, ctx)
                ctx['buf'].write(';')
                ctx['buf'].newline()
            else:
                self._gen_anode(snd, 'prim', ctx)

    def _gen_anode_label__prim(self, nd, ctx):
        oidt = ctx['buf'].popindent()
        ctx['buf'].write(f'@lab.{nd.name}:')
        ctx['buf'].newline()
        ctx['buf'].indent(oidt)

    # act

    def _gen_anode_act__prim(self, nd, ctx):
        self._gen_anode_act(nd, ctx)
        ctx['buf'].write(';')
        ctx['buf'].newline()

    def _gen_anode_act(self, nd, ctx):
        ctx['buf'].write(nd.name)
        ctx['buf'].write('(')
        self._gen_vnode_args(nd.subs, ctx)
        ctx['buf'].write(')')

    def _gen_vnode_args(self, subs, ctx):
        buf = ctx['buf']
        for i, bnd in enumerate(subs):
            snd = self._getone(bnd)
            self._gen_anode(snd, None, ctx)
            if i < len(subs) - 1:
                buf.write(', ')

    def _gen_anode_act_pop__prim(self, nd, ctx):
        snd = self._getone(self._getone(nd))
        self._gen_anode(snd, None, ctx)
        ctx['buf'].write(';')
        ctx['buf'].newline()

    def _gen_anode_act_push(self, nd, ctx):
        snd = self._getone(self._getone(nd))
        self._gen_anode(snd, None, ctx)

    def _gen_anode_act_return__prim(self, nd, ctx):
        ar = []
        for i, bnd in enumerate(nd.subs):
            an = f'ret{i+1}'
            ctx['buf'].write(f'{an} = ')
            ar.append(an)
            self._gen_anode(bnd, 'inret', ctx)
        ctx['buf'].write(f'return {", ".join(ar)}')
        ctx['buf'].write(';')
        ctx['buf'].newline()

    def _gen_anode_act_call__prim(self, nd, ctx):
        self._gen_anode_act_call(nd, ctx)
        ctx['buf'].write(';')
        ctx['buf'].newline()

    def _gen_anode_act_call(self, nd, ctx):
        subs = nd.subs.copy()
        dnd = self._getone(subs.pop())
        if nd.name == 'syscall':
            dname = f'sys.{dnd.name}'
        elif nd.name == 'txtcall':
            self._gen_vnode_text(dnd, ctx)
            return
        else:
            dname = f'fun.{dnd.name}'
        ctx['buf'].write(dname)
        ctx['buf'].write('(')
        self._gen_vnode_args(subs, ctx)
        ctx['buf'].write(')')

    def _gen_vnode_text(self, nd, ctx):
        if not nd.name in ctx['text']:
            self._error(nd, f'unknown text: {nd.name}')
        txt = ctx['text'][nd.name]
        ctx['buf'].write(f'text = "{txt}"')

    def _gen_anode_act_halloc__prim(self, nd, ctx):
        ctx['buf'].write('local = heap[')
        self._gen_anode(self._getone(self._getone(nd)), None, ctx)
        ctx['buf'].write('];')
        ctx['buf'].newline()

    def _gen_anode_act_hfree__prim(self, nd, ctx):
        ctx['buf'].write('free heap[')
        self._gen_anode(self._getone(self._getone(nd)), None, ctx)
        ctx['buf'].write('];')
        ctx['buf'].newline()

    def _gen_anode_act_hpush(self, nd, ctx):
        ctx['buf'].write('local')

    def _gen_vnode_var(self, nd, ctx):
        ctx['buf'].write('[')
        self._gen_anode(self._getone(nd), None, ctx)
        ctx['buf'].write(']')

    def _gen_anode_act_vget(self, nd, ctx):
        ctx['buf'].write('var')
        self._gen_vnode_var(self._getone(nd), ctx)

    def _gen_anode_act_vset(self, nd, ctx):
        ndl, ndr = nd.subs
        if (getattr(self._getone(ndl), 'name', None) == 'push'
            and self._getone(self._getone(self._getone(ndl))).__class__.__name__ == 'c_script_anode_inst'
            and (self._getone(self._getone(self._getone(ndl))).val & 0x1f)):
            print('here2', nd.addr, nd)
        ctx['buf'].write('var')
        self._gen_vnode_var(ndl, ctx)
        ctx['buf'].write(' = ')
        self._gen_anode(self._getone(ndr), None, ctx)

    def _gen_anode_act_vmask(self, nd, ctx):
        ndl, ndr = nd.subs
        ctx['buf'].write('flag')
        self._gen_vnode_var(ndl, ctx)
        ctx['buf'].write(' = ')
        self._gen_anode(self._getone(ndr), None, ctx)

    def _gen_anode_act_vcheck(self, nd, ctx):
        ctx['buf'].write('flag')
        self._gen_vnode_var(self._getone(nd), ctx)

    # calc

    def _gen_vnode_act_calc_1(self, op, nd, ctx):
        ctx['buf'].write('-')
        self._gen_anode(self._getone(nd), None, ctx)

    def _gen_vnode_act_calc_2(self, op, nd1, nd2, ctx):
        ctx['buf'].write(f'(')
        self._gen_anode(self._getone(nd1), None, ctx)
        ctx['buf'].write(f' {op} ')
        self._gen_anode(self._getone(nd2), None, ctx)
        ctx['buf'].write(f')')

    def _gen_anode_act_calc_add(self, nd, ctx):
        self._gen_vnode_act_calc_2('+', *nd.subs, ctx)

    def _gen_anode_act_calc_sub(self, nd, ctx):
        self._gen_vnode_act_calc_2('-', *nd.subs, ctx)

    def _gen_anode_act_calc_mul(self, nd, ctx):
        self._gen_vnode_act_calc_2('*', *nd.subs, ctx)

    def _gen_anode_act_calc_div(self, nd, ctx):
        self._gen_vnode_act_calc_2('//', *nd.subs, ctx)

    def _gen_anode_act_calc_mod(self, nd, ctx):
        self._gen_vnode_act_calc_2('%', *nd.subs, ctx)

    def _gen_anode_act_calc_neg(self, nd, ctx):
        self._gen_vnode_act_calc_1('-', *nd.subs, ctx)

    def _gen_anode_act_calc_eq(self, nd, ctx):
        self._gen_vnode_act_calc_2('==', *nd.subs, ctx)

    def _gen_anode_act_calc_gt(self, nd, ctx):
        self._gen_vnode_act_calc_2('>', *nd.subs, ctx)

    def _gen_anode_act_calc_ge(self, nd, ctx):
        self._gen_vnode_act_calc_2('>=', *nd.subs, ctx)

    def _gen_anode_act_calc_lt(self, nd, ctx):
        self._gen_vnode_act_calc_2('<', *nd.subs, ctx)

    def _gen_anode_act_calc_le(self, nd, ctx):
        self._gen_vnode_act_calc_2('<=', *nd.subs, ctx)

    def _gen_anode_act_calc_ne(self, nd, ctx):
        self._gen_vnode_act_calc_2('!=', *nd.subs, ctx)

    def _gen_anode_act_calc_and(self, nd, ctx):
        self._gen_vnode_act_calc_2('&&', *nd.subs, ctx)

    def _gen_anode_act_calc_or(self, nd, ctx):
        self._gen_vnode_act_calc_2('||', *nd.subs, ctx)

    def _gen_anode_act_calc_band(self, nd, ctx):
        self._gen_vnode_act_calc_2('&', *nd.subs, ctx)

    def _gen_anode_act_calc_bor(self, nd, ctx):
        self._gen_vnode_act_calc_2('|', *nd.subs, ctx)

    def _gen_anode_act_calc_bxor(self, nd, ctx):
        self._gen_vnode_act_calc_2('^', *nd.subs, ctx)

    def _gen_anode_act_calc_shl(self, nd, ctx):
        self._gen_vnode_act_calc_2('<<', *nd.subs, ctx)

    def _gen_anode_act_calc_shr(self, nd, ctx):
        self._gen_vnode_act_calc_2('>>', *nd.subs, ctx)

    # ref

    def _gen_anode_ref_func(self, nd, ctx):
        ctx['buf'].write(str(nd))

    def _gen_anode_ref_label(self, nd, ctx):
        ctx['buf'].write(str(nd))

    def _gen_anode_parm(self, nd, ctx):
        ctx['buf'].write(str(nd))

    def _gen_anode_inst(self, nd, ctx):
        val = nd.val
        if val & 0x4000000:
            val -= 0x8000000
        ctx['buf'].write(hex(val))

    def gen_code(self):
        self._gen_anode(self.ast)

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
        cd = c_scode_program(ast, c_scode_buf_null())
        cd.gen_code()
    tst1()
