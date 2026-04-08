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
        return c_scode_buf(self, False, idt)

    def indent(self, val):
        self.idt += val
        if self.idt < 0:
            raise err_scode_syntax('indent underflow')

    def noindent(self):
        idt = self.idt
        self.idt = 0
        return idt

    def _idtsym(self, idt):
        return (self.IDTSYM for _ in range(idt))

    def _writeline(self, line):
        if self.tch:
            self.par.write(line)
            self.par.newline()
        else:
            self.buf.append(line)

    def write(self, s):
        self.lbuf.append(s)

    def newline(self):
        if self.lbuf:
            line = ''.join((*self._idtsym(self.idt), *self.lbuf))
            self.lbuf = []
        else:
            line = ''
        self._writeline(line)

    HDIDX = 0
    def hold(self):
        if self.tch:
            raise err_scode_syntax('touched buf unholdable')
        elif self.lbuf:
            raise err_scode_syntax('can only hold a newline')
        c_scode_buf.HDIDX += 1
        self._writeline((c_scode_buf.HDIDX, self.idt))

    def reput(self, hid, line):
        if self.tch:
            raise err_scode_syntax('touched buf unchangable')
        for i, (dhid, didt) in enumerate(self.buf):
            if dhid == hid:
                break
        else:
            raise err_scode_syntax(f'invalid hid: {hid}')
        self.buf[i] = ''.join((*self._idtsym(didt), line))

    def touch(self):
        if self.tch:
            return self
        self.tch = True
        if not self.par:
            return self
        for line in self.buf:
            if isinstance(line, tuple):
                hid, hidt = line
                self.par._writeline((hid, self.par.idt + hidt))
            else:
                self.par.write(line)
                self.par.newline()
        self.buf = []
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

class c_scode_buf_fd(c_scode_buf):

    def __init__(self, fd):
        super().__init__(None, True, 0)
        self.fd = fd

    def _writeline(self, line):
        self.fd.write(line + '\n')

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
                breakpoint()

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
        ctx['bstack'] = []
        ctx['labset'] = (set(), set(), set())
        ctx['unkjmp'] = {}
        self._gen_anode(nd.sub, 'prim', ctx)
        buf.touch()
        if len(ctx.pop('bstack')) != 0:
            self._error(nd, 'function block unbalance')
        if sum(len(s) for s in ctx.pop('labset')[:2]) != 0:
            self._error(nd, 'function label unmatch')
        if ctx.pop('unkjmp'):
            self._error(nd, 'function with unknown jump')
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

    def _gen_anode_nop__prim(self, nd, ctx):
        ctx['buf'].write('nop;')
        ctx['buf'].newline()

    def _gen_anode_pass__prim(self, nd, ctx):
        ctx['buf'].write('pass;')
        ctx['buf'].newline()

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

    def _gen_anode_act_vget(self, nd, ctx):
        ctx['buf'].write('var')
        ctx['buf'].write('[')
        self._gen_anode(self._getone(self._getone(nd)), None, ctx)
        ctx['buf'].write(' >>5]')

    def _gen_anode_act_vset(self, nd, ctx):
        ndr, ndl = nd.subs
        ctx['buf'].write('var')
        ctx['buf'].write('[')
        self._gen_anode(self._getone(ndl), None, ctx)
        ctx['buf'].write(' >>5]')
        ctx['buf'].write(' = ')
        self._gen_anode(self._getone(ndr), None, ctx)

    def _gen_anode_act_vmask(self, nd, ctx):
        ndr, ndl = nd.subs
        ctx['buf'].write('flag')
        ctx['buf'].write('[')
        self._gen_anode(self._getone(ndl), None, ctx)
        ctx['buf'].write(']')
        ctx['buf'].write(' = ')
        self._gen_anode(self._getone(ndr), None, ctx)

    def _gen_anode_act_vcheck(self, nd, ctx):
        ctx['buf'].write('flag')
        ctx['buf'].write('[')
        self._gen_anode(self._getone(self._getone(nd)), None, ctx)
        ctx['buf'].write(']')

    # flow

    def _use_label_in_ctx(self, addr, ctx):
        lbunused, lbneed, lbdone = ctx['labset']
        if not addr in lbdone:
            if addr in lbunused:
                lbunused.remove(addr)
                lbdone.add(addr)
            else:
                lbneed.add(addr)

    def _gen_anode_label__prim(self, nd, ctx):
        buf = ctx['buf']
        lbunused, lbneed, lbdone = ctx['labset']
        if nd.addr in lbdone:
            # poped by while done
            assert not nd.addr in lbneed
        elif nd.addr in lbneed:
            lbneed.remove(nd.addr)
            lbdone.add(nd.addr)
        else:
            lbunused.add(nd.addr)
        bstack = ctx['bstack']
        poped = False
        while bstack:
            saddr, daddr, bnt, pbuf = bstack[-1]
            if daddr < nd.addr:
                self._error(nd, f'no-end if-block at: {daddr:x}')
            elif daddr > nd.addr:
                break
            assert buf.par == pbuf and not buf.tch
            if bnt:
                pbuf.write('if not')
            else:
                pbuf.write('if')
            buf.indent(-1)
            buf.write('}')
            buf.newline()
            buf.touch()
            poped = True
            self._use_label_in_ctx(nd.addr, ctx)
            bstack.pop()
            buf = ctx['buf'] = pbuf
        if not poped:
            oidt = ctx['buf'].noindent()
            ctx['buf'].write(f'@lab.{nd.name}:')
            ctx['buf'].newline()
            ctx['buf'].indent(oidt)

    def _gen_anode_act_jump__prim(self, nd, ctx):
        lb = self._getone(self._getone(nd))
        buf = ctx['buf']
        bstack = ctx['bstack']
        if bstack:
            saddr, daddr, bnt, pbuf = bstack[-1]
            if daddr == nd.addr + 1:
                if lb.addr == saddr - 2:
                    assert buf.par == pbuf and not buf.tch
                    if bnt:
                        pbuf.write('while')
                    else:
                        pbuf.write('while not')
                    buf.indent(-1)
                    buf.write('}')
                    buf.newline()
                    buf.touch()
                    self._use_label_in_ctx(lb.addr, ctx)
                    self._use_label_in_ctx(daddr, ctx)
                    bstack.pop()
                    buf = ctx['buf'] = pbuf
                    return
        hid = buf.hold()
        ctx['unkjmp'][lb.addr] =(nd.addr, hid)

    def _gen_vnode_if(self, nt, nd, ctx):
        condi, lb = (self._getone(i) for i in nd.subs)
        if lb.addr <= nd.addr:
            self._error(nd, f'if-block should not be before jump')
        bstack = ctx['bstack']
        if bstack and bstack[-1][1] < lb.addr:
            self._error(nd, f'if-block out of bounds: {lb}')
        pbuf = ctx['buf']
        bstack.append((nd.addr, lb.addr, nt, pbuf))
        buf = ctx['buf'] = pbuf.sub()
        idt = buf.noindent()
        buf.write('(')
        self._gen_anode(condi, None, ctx)
        buf.write(') {')
        buf.newline()
        buf.indent(idt)

    def _gen_anode_act_jump_if__prim(self, nd, ctx):
        self._gen_vnode_if(False, nd, ctx)

    def _gen_anode_act_jump_if_not__prim(self, nd, ctx):
        self._gen_vnode_if(True, nd, ctx)

    # calc

    def _gen_vnode_act_calc_1(self, op, nd, ctx):
        ctx['buf'].write('(')
        ctx['buf'].write('-')
        self._gen_anode(self._getone(nd), None, ctx)
        ctx['buf'].write(')')

    def _gen_vnode_act_calc_2(self, op, nd1, nd2, ctx):
        ctx['buf'].write('(')
        self._gen_anode(self._getone(nd1), None, ctx)
        ctx['buf'].write(f' {op} ')
        self._gen_anode(self._getone(nd2), None, ctx)
        ctx['buf'].write(')')

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
        if True:
            #cd = c_scode_program(ast, c_scode_buf_null())
            cd = c_scode_program(ast, c_scode_buf_std())
            cd.gen_code()
        else:
            with open(r'wktab\output.txt', 'w', encoding = 'utf-8') as fd:
                cd = c_scode_program(ast, c_scode_buf_fd(fd))
                cd.gen_code()
    tst1()
