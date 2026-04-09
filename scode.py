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
        return c_scode_buf.HDIDX

    def reput(self, hid, line, idt_shft = 0, idt = None):
        if self.tch:
            raise err_scode_syntax('touched buf unchangable')
        for i, v in enumerate(self.buf):
            if not isinstance(v, tuple):
                continue
            dhid, didt = v
            if dhid == hid:
                break
        else:
            raise err_scode_syntax(f'invalid hid: {hid}')
        if line is None:
            self.buf.pop(i)
        else:
            self.buf[i] = ''.join((*self._idtsym(
                max(0, didt + idt_shft) if idt is None else idt
            ), line))

    def touch(self):
        if self.tch:
            return self
        self.tch = True
        if not self.par:
            return self
        for line in self.buf:
            if isinstance(line, tuple):
                if self.par.tch:
                    raise err_scode_syntax('touched parbuf unholdable')
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

def with_anode(*stricts):
    def _deco(cls):
        nmset = set()
        for mn in dir(cls):
            if not mn.startswith('_gen_anode_'):
                continue
            nm = mn.split('__')[0]
            nmset.add(nm)
        def _dispatch_anode(self, nd, assume):
            ctype = nd.__class__.__name__
            assert ctype.startswith('c_script_anode_')
            nm1 = '_gen_anode_' + ctype[len('c_script_anode_'):]
            nm = nm1
            if hasattr(nd, 'name'):
                nm2 = '_'.join((nm, nd.name))
                if nm2 in nmset:
                    nm = nm2
            if assume:
                nm = '__'.join((nm, assume))
                if not hasattr(self, nm) and not assume in stricts:
                    nm = '__'.join((nm1, assume))
            return getattr(self, nm, None), nm[len('_gen_anode_'):]
        cls._dispatch_anode = _dispatch_anode
        return cls
    return _deco

@with_anode('prim')
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

    def _gen_any_anode(self, nd, assumes, ctx = None):
        for assume in assumes:
            mth, mn = self._dispatch_anode(nd, assume)
            if mth:
                mth(nd, ctx)
                return mn, assume
        self._error(nd, f'should not be assumed as: {mn} / {assumes}')

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
        ctx['lbrvs'] = {}
        ctx['holes'] = []
        self._gen_anode(nd.sub, 'lbscan', ctx)
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
        ctx['lbhld'] = {}
        self._gen_anode(nd.sub, 'prim', ctx)
        bstack = ctx.pop('bstack')
        if bstack:
            self._error(nd, f'function block unbalance: {bstack}')
        sus_lhld = None
        for laddr, (lhid, lbv, lkp) in sorted(
                ctx.pop('lbhld').items(), key = lambda v: v[0]):
            if lkp == 'lookahead':
                sus_lhld = (lhid, lbv)
            elif lkp:
                if sus_lhld:
                    buf.reput(*sus_lhld, None, 0)
                    sus_lhld = None
                buf.reput(lhid, lbv, None, 0)
            else:
                if sus_lhld:
                    buf.reput(sus_lhld[0], None)
                    sus_lhld = None
                buf.reput(lhid, None)
        if sus_lhld:
            buf.reput(sus_lhld[0], None)
            sus_lhld = None
        buf.touch()
        ctx['buf'] = pbuf
        pbuf.write('}')
        pbuf.newline()
        ctx.pop('holes')
        ctx.pop('lbrvs')

    def _gen_anode_text(self, nd, ctx):
        pass

    def _gen_anode_bat__prim(self, nd, ctx):
        ctx['prv_addr'] = -1
        for snd in nd.subs:
            if self._chk_holes(snd.addr, ctx):
                _, am = self._gen_any_anode(snd, ('prim', None), ctx)
                if am == None:
                    ctx['buf'].write(';')
                    ctx['buf'].newline()
            else:
                self._gen_anode(snd, 'prim', ctx)
            ctx['prv_addr'] = snd.addr

    # label scan

    def _gen_anode_bat__lbscan(self, nd, ctx):
        ctx['lbseq'] = []
        lst_addr = 0
        for snd in nd.subs:
            self._gen_anode(snd, 'lbscan', ctx)
            lst_addr = snd.addr
        lbrvs = ctx['lbrvs']
        holes = ctx['holes']
        lbseq = ctx.pop('lbseq')
        ishole = False
        hole_st = None
        for la in lbseq:
            if ishole:
                if la in lbrvs:
                    holes.append((hole_st, la))
                    ishole = False
            else:
                if not la in lbrvs:
                    hole_st = la
                    ishole = True
        if ishole:
            holes.append((hole_st, lst_addr + 1))

    def _chk_holes(self, addr, ctx):
        holes = ctx['holes']
        for st, ed in holes:
            if st <= addr < ed:
                return True
        return False

    def _gen_anode_act__lbscan(self, nd, ctx):
        pass

    def _gen_anode_label__lbscan(self, nd, ctx):
        ctx['lbseq'].append(nd.addr)

    def _gen_anode_act_call__lbscan(self, nd, ctx):
        pass

    def _rec_label_reverse(self, saddr, daddr, jtyp, ctx):
        lbrvs = ctx['lbrvs']
        if not daddr in lbrvs:
            lbrvs[daddr] = {}
        lbrvs[daddr][saddr] = jtyp

    def _chk_label_reverse(self, saddr, daddr, ctx):
        lbrvs = ctx['lbrvs']
        if not daddr in lbrvs:
            return None
        return lbrvs[daddr].get(saddr, None)

    def _gen_anode_act_jump__lbscan(self, nd, ctx):
        lb = self._getone(self._getone(nd))
        self._rec_label_reverse(nd.addr, lb.addr, 'j', ctx)

    def _gen_anode_act_jump_if__lbscan(self, nd, ctx):
        condi, lb = (self._getone(i) for i in nd.subs)
        self._rec_label_reverse(nd.addr, lb.addr, 'jt', ctx)

    def _gen_anode_act_jump_if_not__lbscan(self, nd, ctx):
        condi, lb = (self._getone(i) for i in nd.subs)
        self._rec_label_reverse(nd.addr, lb.addr, 'jf', ctx)

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

    def _gen_anode_act_setrval__prim(self, nd, ctx):
        ridx, sub = (self._getone(i) for i in nd.subs)
        ctx['buf'].write(f'ret{ridx.val+1} = ')
        self._gen_anode(sub, None, ctx)
        ctx['buf'].write(';')
        ctx['buf'].newline()

    def _gen_anode_act_return__prim(self, nd, ctx):
        rnum = self._getone(self._getone(nd)).val
        ar = [f'ret{i+1}' for i in range(rnum)]
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

    def _peek_bstack(self, addr, dbtyp, ctx):
        bstack = ctx['bstack']
        if not bstack:
            return None, None
        mbsinfo = bstack[-1]
        btyp, paddr, saddr, daddr, pbuf = mbsinfo
        assert ctx['buf'].par == pbuf and not ctx['buf'].tch
        if addr > daddr:
            return False, False
        elif addr < daddr:
            mbsinfo = None
        for bsinfo in reversed(bstack):
            btyp, paddr, saddr, daddr, pbuf = bsinfo
            if dbtyp is None or btyp == dbtyp:
                return mbsinfo, bsinfo
        else:
            return mbsinfo, None

    def _check_bstack_bound(self, addr, shft, ctx):
        bstack = ctx['bstack']
        if len(bstack) <= shft:
            return True
        btyp, paddr, saddr, daddr, pbuf = bstack[-1-shft]
        if btyp == 'lp':
            return addr <= daddr - 2
        else:
            return addr <= daddr

    def _gen_anode_label__prim(self, nd, ctx):
        buf = ctx['buf']
        while True:
            mbsinfo, _ = self._peek_bstack(nd.addr, None, ctx)
            if mbsinfo:
                btyp, paddr, saddr, daddr, pbuf = mbsinfo
                assert btyp != 'lp'
                buf.touch()
                ctx['bstack'].pop()
                buf = ctx['buf'] = pbuf
                buf.write('}')
                buf.newline()
            elif mbsinfo is False:
                self._error(nd, 'exceed no-end block')
            else:
                break
        lbhld = ctx['lbhld']
        if not nd.addr in ctx['lbrvs']:
            assert not nd.addr in lbhld
            lbhld[nd.addr] = [buf.hold(), f'@hol.{nd.addr:x}:', 'lookahead']
            return
        if nd.addr in lbhld:
            lbhinfo = lbhld[nd.addr]
            assert lbhld[nd.addr][0] is None and lbhinfo[2]
        else:
            lbhinfo = lbhld[nd.addr] = [None, None, False]
        lbhld[nd.addr][0] = buf.hold()
        lbhld[nd.addr][1] = f'@lab.{nd.addr:x}:'

    def _gen_anode_act_jump__prim(self, nd, ctx):
        lb = self._getone(self._getone(nd))
        buf = ctx['buf']
        mbsinfo, bsinfo = self._peek_bstack(nd.addr + 1, 'lp', ctx)
        if mbsinfo:
            btyp, paddr, saddr, daddr, pbuf = mbsinfo
            if btyp == 'lp':
                assert lb.addr == paddr
                buf.touch()
                ctx['bstack'].pop()
                buf = ctx['buf'] = pbuf
                buf.write('}')
                buf.newline()
                return
            elif btyp == 'if' and self._check_bstack_bound(lb.addr, 1, ctx):
                buf.touch()
                ctx['bstack'].pop()
                buf = ctx['buf'] = pbuf
                buf.write('} else {')
                buf.newline()
                ctx['bstack'].append(('el', ctx['prv_addr'], nd.addr, lb.addr, buf))
                ctx['buf'] = buf.sub()
                return
        if bsinfo:
            btyp, paddr, saddr, daddr, pbuf = bsinfo
            assert btyp == 'lp'
            if lb.addr == daddr:
                buf.write('break;')
                buf.newline()
                return
            elif lb.addr == daddr - 2:
                buf.write('continue;')
                buf.newline()
                return
            else:
                self._warn(nd, f'unparsable jump: {nd}')
        elif bsinfo is None:
            self._warn(nd, f'isolated jump: {nd}')
        else:
            self._error(nd, 'exceed no-end block')
        lbhld = ctx['lbhld']
        if lb.addr in lbhld:
            lbhld[lb.addr][2] = True
        else:
            lbhld[lb.addr] = [None, None, True]
        buf.write('jump(')
        self._gen_anode(lb, None, ctx)
        buf.write(');')
        buf.newline()

    def _gen_vnode_if(self, nt, nd, ctx):
        condi, lb = (self._getone(i) for i in nd.subs)
        if lb.addr <= nd.addr:
            self._error(nd, f'if-block should not be before jump')
        lbrvs = ctx['lbrvs']
        djtyp = self._chk_label_reverse(lb.addr - 1, ctx['prv_addr'], ctx)
        buf = ctx['buf']
        if djtyp:
            if djtyp != 'j':
                self._error(nd, f'while-block should not be end with condi')
            buf.write('while ')
            btyp = 'lp'
        else:
            buf.write('if ')
            btyp = 'if'
        if not nt:
            buf.write('not ')
        buf.write('(')
        self._gen_anode(condi, None, ctx)
        buf.write(') {')
        buf.newline()
        bstack = ctx['bstack']
        if bstack and bstack[-1][3] < lb.addr:
            self._error(nd, f'block out of bounds: {lb}')
        bstack.append((btyp, ctx['prv_addr'], nd.addr, lb.addr, buf))
        ctx['buf'] = buf.sub()

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
        if False:
            #cd = c_scode_program(ast, c_scode_buf_null())
            cd = c_scode_program(ast, c_scode_buf_std())
            cd.gen_code()
        else:
            with open(r'wktab\output.txt', 'w', encoding = 'utf-8') as fd:
                cd = c_scode_program(ast, c_scode_buf_fd(fd))
                cd.gen_code()
    tst1()
