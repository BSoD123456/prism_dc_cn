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
        self.hold_ref = {}

    def sub(self, idt = 1):
        return c_scode_buf(self, False, idt)

    def sub_inline(self):
        return c_scode_buf_inline(self, False)

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

    def _conltoks(self, ltoks):
        return ''.join(str(t) for t in ltoks)

    def _mergeltoks(self, ltoks):
        arls = []
        rls = ['__head']
        scnt = 0
        idt = 0
        for tok in ltoks:
            if isinstance(tok, tuple):
                cmd = tok[0]
                if cmd == 'idt':
                    idt += tok[1]
                    rls.extend(self._idtsym(tok[1]))
                elif cmd == 'disline':
                    if scnt == 0:
                        break
                elif cmd == '__sepline':
                    arls.extend(rls)
                    rls = ['\n']
                    scnt = 0
                    rls.extend(self._idtsym(idt))
            else:
                rls.append(tok)
                scnt += 1
        else:
            arls.extend(rls)
        return self._conltoks(arls[1:]) if arls else None

    def _flushltoks(self, ltoks, nl):
        for tok in ltoks:
            if isinstance(tok, tuple):
                self.par.meta(*tok)
            else:
                self.par.write(tok)
        if nl:
            self.par.newline()

    def _writeltoks(self, ltoks):
        if self.tch:
            self._flushltoks(ltoks, True)
        else:
            self.buf.append(ltoks)

    def meta(self, cmd, *args):
        self.lbuf.append((cmd, *args))

    def write(self, s):
        self.lbuf.append(s)

    def newline(self):
        sltoks = self.lbuf
        self.lbuf = []
        if sltoks:
            nidt = self.idt
            for i in range(len(sltoks)):
                tok = sltoks[i]
                if isinstance(tok, tuple) and tok[0] == 'idt':
                    nidt += tok[1]
                else:
                    break
            self.meta('idt', nidt)
            self.lbuf.extend(sltoks[i:])
        self._writeltoks(self.lbuf)
        self.lbuf = []

    HDIDX = 0
    def hold(self, idt_or_inline):
        if self.tch:
            raise err_scode_syntax('touched buf unholdable')
        inline = (idt_or_inline is None)
        if not inline:
            if self.lbuf:
                raise err_scode_syntax('can only hold a newline withou inline')
            self.meta('idt', idt_or_inline)
        c_scode_buf.HDIDX += 1
        self.meta('hold', c_scode_buf.HDIDX)
        self.hold_ref[c_scode_buf.HDIDX] = len(self.buf)
        if not inline:
            self.meta('disline')
            self.newline()
        return c_scode_buf.HDIDX

    def reput(self, hid, tok, strict = False, rehold = False):
        if self.tch:
            raise err_scode_syntax('touched buf unchangable')
        if not hid in self.hold_ref:
            raise err_scode_syntax(f'invalid hid: {hid}')
        if rehold and tok is None:
            return
        bi = self.hold_ref[hid]
        if bi >= len(self.buf):
            assert bi == len(self.buf)
            bi = None
            ltoks = self.lbuf
        else:
            ltoks = self.buf[bi]
        for li in range(len(ltoks)-1, -1, -1):
            ttok = ltoks[li]
            if not isinstance(ttok, tuple) or ttok[0] != 'hold':
                continue
            if ttok[1] == hid:
                break
        else:
            if strict:
                raise err_scode_syntax(f'hold ref unmatched: {hid}')
            else:
                self.hold_ref.pop(hid)
                return
        if not rehold:
            self.hold_ref.pop(hid)
        if tok is None:
            assert not rehold
            ltoks.pop(li)
        elif isinstance(tok, str):
            if rehold:
                ltoks.insert(li, tok)
            else:
                ltoks[li] = tok
        else:
            if not rehold:
                ltoks.pop(li)
            for i, stok in enumerate(tok):
                ltoks.insert(li + i * 2, stok)
                ltoks.insert(li + i * 2 + 1, ('__sepline',))

    def flush(self):
        if self.tch:
            return False
        if not self.par:
            return True
        if self.par.lbuf:
            raise err_scode_syntax('should touch a parent with newline')
        elif self.lbuf:
            raise err_scode_syntax('should be touched with newline')
        blen = len(self.par.buf)
        self.par.hold_ref.update(
            (hid, hbi + blen)
            for hid, hbi in self.hold_ref.items())
        for ltoks in self.buf:
            self._flushltoks(ltoks, True)
        self.buf = []
        return True

    def touch(self):
        if self.flush():
            self.tch = True
        return self

class c_scode_buf_inline(c_scode_buf):

    def __init__(self, parent, touched):
        super().__init__(parent, touched, 0)

    def sub(self, idt = 1):
        raise NotImplementedError('buf inline should not do this')

    def indent(self, val):
        raise NotImplementedError('buf inline should not do this')

    def noindent(self):
        raise NotImplementedError('buf inline should not do this')

    def newline(self):
        raise NotImplementedError('buf inline should not do this')

    def flush(self):
        if self.tch:
            return False
        if not self.par:
            return True
        self._flushltoks(self.lbuf, False)
        self.lbuf = []
        return True

class c_scode_buf_null(c_scode_buf):

    def __init__(self):
        super().__init__(None, True, 0)

    def _writeltoks(self, ltoks):
        pass

    def meta(self, cmd, *args):
        if cmd == 'hold':
            raise err_scode_syntax(f'unsolved held token: {args[0]}')
        super().meta(cmd, *args)

class c_scode_buf_std(c_scode_buf_null):

    def _writeltoks(self, ltoks):
        line = self._mergeltoks(ltoks)
        if not line is None:
            print(line)

class c_scode_buf_fd(c_scode_buf_null):

    def __init__(self, fd):
        super().__init__()
        self.fd = fd

    def _writeltoks(self, ltoks):
        line = self._mergeltoks(ltoks)
        if not line is None:
            self.fd.write(line + '\n')

def with_anode(*stricts):
    def _deco(cls):
        nmset = set()
        for mn in dir(cls):
            if not mn.startswith('_gen_anode_'):
                continue
            nms = mn.split('__')
            if len(nms) < 2 or nms[1] in stricts:
                nmset.add(nms[0])
        def _dispatch_anode(self, nd, assume):
            ctype = nd.__class__.__name__
            assert ctype.startswith('c_script_anode_')
            nm1 = '_gen_anode_' + ctype[len('c_script_anode_'):]
            nm = nm1
            if hasattr(nd, 'name'):
                nm2 = '_'.join((nm, nd.name))
                if nm2 in nmset or (assume and not assume in stricts):
                    nm = nm2
            if assume:
                nm = '__'.join((nm, assume))
                if not hasattr(self, nm) and not assume in stricts:
                    nm = '__'.join((nm1, assume))
            return getattr(self, nm, None), nm[len('_gen_anode_'):]
        cls._dispatch_anode = _dispatch_anode
        return cls
    return _deco

class c_scode_parser:

    def __init__(self, ast, buf, conf = None):
        self.ast = ast
        self.buf = buf
        self.conf = {} if conf is None else conf

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

    def _gen_optkargs_anode(self, nd, assume = None, ctx = None, **ka):
        mth, mn = self._dispatch_anode(nd, assume)
        if not mth:
            self._error(nd, f'should not be assumed as: {mn}')
        if mth.__code__.co_flags & 0x8:
            mth(nd, ctx, **ka)
        else:
            mth(nd, ctx)
        return mn

    def gen_code(self):
        self._gen_anode(self.ast)

@with_anode('prim', 'intext')
class c_scode_program(c_scode_parser):

    SC_TXT_INLINE = {
        'get_name', 'get_ctrl', }
    SC_TXT_DONE = {
        'set_name',
        'print_text', 'print_text_choose', 'print_text_continue', }

    def __init__(self, ast, buf, conf = None):
        dconf = {
            'reduce_calc': True,
            'output_restab': False, }
        if conf:
            dconf = {**dconf, **conf}
        super().__init__(ast, buf, dconf)
        self.chrset = c_charset_jp()

    # program

    def _gen_anode_prog(self, nd, ctx):
        ctx = {}
        ctx['restab'] = {
            'func': {},
            'text': {},}
        rtbuf = ctx['buf'] = self.buf.sub(0)
        for snd in nd.subs:
            self._gen_anode(snd, 'restab', ctx)
        buf = ctx['buf'] = self.buf
        ctx['ftxt'] = {}
        self._gen_anode(nd, 'ivkscan', ctx)
        buf.meta('start', 'prog')
        buf.meta('disline')
        buf.newline()
        for snd in nd.subs:
            if self._gen_anode(snd, None, ctx) == 'func':
                buf.newline()
        buf.meta('end', 'prog')
        buf.meta('disline')
        buf.newline()
        buf.meta('start', 'restab')
        buf.meta('disline')
        buf.newline()
        if self.conf['output_restab']:
            rtbuf.touch()
        buf.meta('end', 'restab')
        buf.meta('disline')
        buf.newline()

    # resource tab

    def _gen_anode_func__restab(self, nd, ctx):
        ftab = ctx['restab']['func']
        if nd.name in ftab:
            self._error(nd, f'duplicated function name: {nd.name}')
        ftab[nd.name] = nd
        self._gen_vnode_func_proto(nd, ctx)
        ctx['buf'].write(';')
        ctx['buf'].newline()

    def _gen_anode_text__restab(self, nd, ctx):
        ttab = ctx['restab']['text']
        if nd.name in ttab:
            self._error(nd, f'duplicated text name: {nd.name}')
        try:
            txt = self.chrset.decode(nd.text)
        except Exception as ex:
            self._error(nd, ex.args[0])
        ttab[nd.name] = txt
        ctx['buf'].write(f'txt.{nd.name} = "{txt}";')
        ctx['buf'].newline()

    # invoke-order scan

    def _gen_anode_prog__ivkscan(self, nd, ctx):
        ctx['ivkwk'] = set()
        for snd in nd.subs:
            self._gen_anode(snd, 'ivkscan', ctx)
        ctx.pop('ivkwk')

    def _gen_anode_text__ivkscan(self, nd, ctx):
        pass

    def _gen_anode_func__ivkscan(self, nd, ctx):
        ivkwk = ctx['ivkwk']
        if nd.addr in ivkwk:
            return
        ftxt = ctx['ftxt']
        fctx = {
            'tsta': 0,
            'ftxt': ftxt,
            'restab': ctx['restab'],
            'buf': ctx['buf'],
            'ivkwk': ivkwk, }
        self._gen_anode(nd.sub, 'ivkscan', fctx)
        ftxt[nd.addr] = fctx['tsta']
        ivkwk.add(nd.addr)

    def _gen_anode_bat__ivkscan(self, nd, ctx):
        for snd in nd.subs:
            self._gen_anode(snd, 'ivkscan', ctx)

    def _set_tsta_lvl(self, lvl, ctx):
        if ctx['tsta'] < lvl:
            ctx['tsta'] = lvl

    def _gen_anode_act__ivkscan(self, nd, ctx):
        self._set_tsta_lvl(0, ctx)

    def _gen_anode_label__ivkscan(self, nd, ctx):
        self._set_tsta_lvl(0, ctx)

    def _gen_anode_act_pop__ivkscan(self, nd, ctx):
        snd = self._getone(self._getone(nd))
        self._gen_anode(snd, 'ivkscan', ctx)

    def _gen_anode_act_call__ivkscan(self, nd, ctx):
        assert nd.name == 'call'
        dnd = self._getone(nd.subs[-1])
        if not dnd.addr in ctx['ftxt']:
            self._gen_anode(ctx['restab']['func'][dnd.name], 'ivkscan', ctx)
            assert dnd.addr in ctx['ftxt']
        self._set_tsta_lvl(ctx['ftxt'][dnd.addr], ctx)

    def _gen_anode_act_call_syscall__ivkscan(self, nd, ctx):
        dnd = self._getone(nd.subs[-1])
        if dnd.name in self.SC_TXT_DONE:
            self._set_tsta_lvl(2, ctx)
        elif dnd.name in self.SC_TXT_INLINE:
            self._set_tsta_lvl(1, ctx)

    def _gen_anode_act_call_txtcall__ivkscan(self, nd, ctx):
        self._set_tsta_lvl(1, ctx)

    # struct

    def _gen_vnode_func_proto(self, nd, ctx):
        if nd.rnum == 1:
            rr = 'ret '
        else:
            rr = ', '.join(f'ret{i+1}' for i in range(nd.rnum))
            if nd.rnum > 1:
                rr = rr + ' '
        ar = ', '.join(f'arg{i+1}' for i in range(nd.anum))
        ctx['buf'].write(f'{rr}fun.{nd.name}({ar})')

    def _gen_anode_func(self, nd, ctx):
        ctx['lbrvs'] = {}
        ctx['holes'] = []
        ctx['txtrng'] = []
        self._gen_anode(nd.sub, 'prescan', ctx)
        self._gen_vnode_func_proto(nd, ctx)
        pbuf = ctx['buf']
        pbuf.write(' {')
        pbuf.newline()
        buf = ctx['buf'] = pbuf.sub()
        buf.meta('block', 'func', nd.name)
        buf.meta('disline')
        buf.newline()
        ctx['bstack'] = []
        ctx['lbhld'] = {}
        self._gen_anode(nd.sub, 'prim', ctx)
        bstack = ctx.pop('bstack')
        if bstack:
            self._error(nd, f'function block unbalance: {bstack}')
        sus_lhld = []
        for laddr, (lhid, lbv, lkp) in sorted(
                ctx.pop('lbhld').items(), key = lambda v: v[0]):
            if lkp == 'lookahead':
                sus_lhld.append((lhid, lbv))
            elif lkp:
                if sus_lhld:
                    for slhid, slbv in sus_lhld:
                        buf.reput(slhid, slbv)
                    sus_lhld.clear()
                buf.reput(lhid, lbv)
            else:
                if sus_lhld:
                    for slhid, slbv in sus_lhld:
                        buf.reput(slhid, None)
                    sus_lhld.clear()
                buf.reput(lhid, None)
        if sus_lhld:
            for slhid, slbv in sus_lhld:
                buf.reput(slhid, None)
        buf.touch()
        buf.meta('block_done', 'func', nd.name)
        buf.meta('disline')
        buf.newline()
        ctx['buf'] = pbuf
        pbuf.write('}')
        pbuf.newline()
        ctx.pop('txtrng')
        ctx.pop('holes')
        ctx.pop('lbrvs')

    def _gen_anode_text(self, nd, ctx):
        pass

    def _gen_anode_bat__prim(self, nd, ctx):
        ctx['cur_addr'] = -1
        ctx['prv_addr'] = -1
        for snd in nd.subs:
            ctx['cur_addr'] = snd.addr
            if self._chk_holes(snd.addr, ctx):
                _, am = self._gen_any_anode(snd, ('prim', None), ctx)
                if am == None:
                    ctx['buf'].write(';')
                    ctx['buf'].newline()
            elif self._chk_txtrng(snd.addr, ctx)[0]:
                self._gen_anode(snd, 'intext', ctx)
            else:
                self._gen_anode(snd, 'prim', ctx)
            ctx['prv_addr'] = snd.addr
        ctx.pop('prv_addr')
        ctx.pop('cur_addr')

    # pre-scan

    def _gen_anode_bat__prescan(self, nd, ctx):
        ctx['lbseq'] = []
        ctx['txtage'] = 0
        lst_addr = 0
        for snd in nd.subs:
            if ctx['txtage'] > 0:
                in_text = True
            else:
                in_text = False
            self._gen_anode(snd, 'prescan', ctx)
            if ctx['txtage'] > 0:
                ctx['txtage'] -= 1
                if ctx['txtage'] > 0:
                    if in_text:
                        ctx['txtrng'][-1][1] = snd.addr
                    else:
                        ctx['txtrng'].append([snd.addr, None])
                else:
                    if ctx['txtrng'] and ctx['txtrng'][-1][1] is None:
                        ctx['txtrng'][-1][1] = ctx['txtrng'][-1][0]
            lst_addr = snd.addr
        ctx.pop('txtage')
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
            elif addr < st:
                break
        return False

    def _mtch_holes(self, addr, ctx):
        holes = ctx['holes']
        for st, ed in holes:
            if addr == st:
                return st, ed
            elif addr < st:
                break
        return None

    def _gen_anode_act__prescan(self, nd, ctx):
        pass

    def _gen_anode_label__prescan(self, nd, ctx):
        ctx['lbseq'].append(nd.addr)

    def _gen_anode_act_pop__prescan(self, nd, ctx):
        snd = self._getone(self._getone(nd))
        self._gen_anode(snd, 'prescan', ctx)

    def _gen_anode_act_call__prescan(self, nd, ctx):
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

    def _gen_anode_act_jump__prescan(self, nd, ctx):
        lb = self._getone(self._getone(nd))
        self._rec_label_reverse(nd.addr, lb.addr, 'j', ctx)

    def _gen_anode_act_jump_if__prescan(self, nd, ctx):
        condi, lb = (self._getone(i) for i in nd.subs)
        self._rec_label_reverse(nd.addr, lb.addr, 'jt', ctx)

    def _gen_anode_act_jump_if_not__prescan(self, nd, ctx):
        condi, lb = (self._getone(i) for i in nd.subs)
        self._rec_label_reverse(nd.addr, lb.addr, 'jf', ctx)

    def _chk_txtrng(self, addr, ctx):
        txtrng = ctx['txtrng']
        for st, ed in txtrng:
            if st <= addr <= ed:
                return True, addr == st, addr == ed
            elif addr < st:
                break
        return False, None, None

    def _gen_anode_act_call__prescan(self, nd, ctx):
        assert nd.name == 'call'
        dnd = self._getone(nd.subs[-1])
        tsta = ctx['ftxt'][dnd.addr]
        if tsta == 1:
            ctx['txtage'] = 2

    def _gen_anode_act_call_txtcall__prescan(self, nd, ctx):
        ctx['txtage'] = 2

    def _gen_anode_act_call_syscall__prescan(self, nd, ctx):
        dnd = self._getone(nd.subs[-1])
        if dnd.name in self.SC_TXT_INLINE:
            ctx['txtage'] = 2

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

    def _gen_anode_act_push(self, nd, ctx, **ka):
        snd = self._getone(self._getone(nd))
        self._gen_optkargs_anode(snd, None, ctx, **ka)

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
        self._gen_vnode_call('fun', nd, ctx)

    def _gen_anode_act_call_syscall(self, nd, ctx):
        fname = self._getone(nd.subs[-1]).name
        if fname in self.SC_TXT_DONE:
            ctx['buf'].meta('text_print', fname)
        ctx['buf'].meta('syscall', fname, False)
        self._gen_vnode_call('sys', nd, ctx)
        ctx['buf'].meta('syscall_done', fname, False)

    def _gen_vnode_call(self, prfx, nd, ctx):
        subs = nd.subs.copy()
        dnd = self._getone(subs.pop())
        dname = f'{prfx}.{dnd.name}'
        ctx['buf'].write(dname)
        ctx['buf'].write('(')
        self._gen_vnode_args(subs, ctx)
        ctx['buf'].write(')')

    # text push

    def _gen_anode_act_pop__intext(self, nd, ctx):
        snd = self._getone(self._getone(nd))
        self._gen_anode(snd, 'intext', ctx)

    def _gen_anode_act_call__intext(self, nd, ctx):
        assert nd.name == 'call'
        vtc = self._gen_vnode_text_pre(ctx)
        ctx['buf'].write('{')
        self._gen_vnode_call('fun', nd, ctx)
        ctx['buf'].write('}')
        self._gen_vnode_text_post(vtc, ctx)

    def _gen_anode_act_call_syscall__intext(self, nd, ctx):
        fname = self._getone(nd.subs[-1]).name
        assert fname in self.SC_TXT_INLINE
        vtc = self._gen_vnode_text_pre(ctx)
        ctx['buf'].meta('syscall', fname, True)
        ctx['buf'].write('{')
        self._gen_vnode_call('sys', nd, ctx)
        ctx['buf'].write('}')
        ctx['buf'].meta('syscall_done', fname, True)
        self._gen_vnode_text_post(vtc, ctx)

    def _gen_anode_act_call_txtcall__intext(self, nd, ctx):
        dnd = self._getone(self._getone(nd))
        if not dnd.name in ctx['restab']['text']:
            self._error(nd, f'unknown text: {dnd.name}')
        txt = ctx['restab']['text'][dnd.name]
        vtc = self._gen_vnode_text_pre(ctx)
        ctx['buf'].write(txt)
        self._gen_vnode_text_post(vtc, ctx)

    def _gen_vnode_text_pre(self, ctx):
        in_text, is_thead, is_ttail = self._chk_txtrng(ctx['cur_addr'], ctx)
        assert in_text
        if is_thead:
            ctx['buf'].write(f'text "')
            ctx['buf'].meta('text')
        return is_ttail

    def _gen_vnode_text_post(self, is_ttail, ctx):
        if is_ttail:
            ctx['buf'].meta('text_done')
            ctx['buf'].write(f'";')
            ctx['buf'].newline()

    # heap

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
        self._gen_optkargs_anode(self._getone(self._getone(nd)), None, ctx,
            prv_oplvl = self.CALC_OPLVL['>>'], prv_opdir = 0)
        ctx['buf'].write(' >>5]')

    def _gen_anode_act_vset(self, nd, ctx):
        ndr, ndl = nd.subs
        ctx['buf'].write('var')
        ctx['buf'].write('[')
        self._gen_optkargs_anode(self._getone(ndl), None, ctx,
            prv_oplvl = self.CALC_OPLVL['>>'], prv_opdir = 0)
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
                buf.meta('block_done', btyp)
                buf.meta('disline')
                buf.newline()
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
            lbhld[nd.addr] = [
                buf.hold(-1), f'@hol.{nd.addr:x}:', 'lookahead']
            return
        if nd.addr in lbhld:
            lbhinfo = lbhld[nd.addr]
            assert lbhld[nd.addr][0] is None and lbhinfo[2]
        else:
            lbhinfo = lbhld[nd.addr] = [None, None, False]
        lbhld[nd.addr][0] = buf.hold(-1)
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
                buf.meta('block_done', btyp)
                buf.meta('disline')
                buf.newline()
                ctx['bstack'].pop()
                buf = ctx['buf'] = pbuf
                buf.write('}')
                buf.newline()
                return
            elif btyp == 'if' and self._check_bstack_bound(lb.addr, 1, ctx):
                buf.touch()
                buf.meta('block_done', btyp, 'el')
                buf.meta('disline')
                buf.newline()
                ctx['bstack'].pop()
                buf = ctx['buf'] = pbuf
                buf.write('} else {')
                buf.newline()
                ctx['bstack'].append((
                    'el', ctx['prv_addr'], nd.addr, lb.addr, buf))
                ctx['buf'] = buf.sub()
                ctx['buf'].meta('block', 'el')
                ctx['buf'].meta('disline')
                ctx['buf'].newline()
                return
        if bsinfo:
            btyp, paddr, saddr, daddr, pbuf = bsinfo
            assert btyp == 'lp'
            if lb.addr == daddr:
                buf.write('break;')
                buf.newline()
                buf.meta('lpflow', 'break')
                buf.meta('disline')
                buf.newline()
                return
            elif lb.addr == daddr - 2:
                buf.write('continue;')
                buf.newline()
                buf.meta('lpflow', 'continue')
                buf.meta('disline')
                buf.newline()
                return
            else:
                self._warn(nd, f'unparsable jump: {nd}')
        elif bsinfo is None:
            holerng = self._mtch_holes(nd.addr + 1, ctx)
            if holerng and lb.addr == holerng[1]:
                buf.write('void {')
                buf.newline()
                ctx['bstack'].append((
                    'vo', ctx['prv_addr'], nd.addr, lb.addr, buf))
                ctx['buf'] = buf.sub()
                ctx['buf'].meta('block', 'vo')
                ctx['buf'].meta('disline')
                ctx['buf'].newline()
                return
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
        ctx['buf'].meta('block', btyp)
        ctx['buf'].meta('disline')
        ctx['buf'].newline()

    def _gen_anode_act_jump_if__prim(self, nd, ctx):
        self._gen_vnode_if(False, nd, ctx)

    def _gen_anode_act_jump_if_not__prim(self, nd, ctx):
        self._gen_vnode_if(True, nd, ctx)

    # calc

    CALC_OPDESC = {
        '+' : ('add' , 2, (1, 1), (0, 0)),
        '-' : ('sub' , 2, (0, 1), (0, 0)),
        '*' : ('mul' , 2, (2, 2), (0, 0)),
        '//': ('div' , 2, (2, 1), (0, 1)),
        '%' : ('mod' , 2, (2, 2), (0, 1)),
        '-1': ('neg' , 1, (0,  ), (0,  )),
        '==': ('eq'  , 2, (0, 0), (0, 0)),
        '>' : ('gt'  , 2, (0, 0), (0, 0)),
        '>=': ('ge'  , 2, (0, 0), (0, 0)),
        '<' : ('lt'  , 2, (0, 0), (0, 0)),
        '<=': ('le'  , 2, (0, 0), (0, 0)),
        '!=': ('ne'  , 2, (0, 0), (0, 0)),
        '&&': ('and' , 2, (2, 2), (0, 0)),
        '||': ('or'  , 2, (2, 2), (2, 2)),
        '&' : ('band', 2, (2, 2), (0, 0)),
        '|' : ('bor' , 2, (1, 1), (0, 0)),
        '^' : ('bxor', 2, (0, 0), (0, 0)),
        '<<': ('shl' , 2, (2, 1), (0, 0)),
        '>>': ('shr' , 2, (2, 1), (0, 0)),
    }

    CALC_OPLVL = (lambda lst: {
        op: len(lst) - lv
        for lv, ops in enumerate(lst)
        for op in ops })([
            ['-1'],
            ['*', '//', '%'],
            ['+', '-'],
            ['<<', '>>'],
            ['&'],
            ['^'],
            ['|'],
            ['==', '!=', '<', '>', '<=', '>='],
            ['&&'],
            ['||'],
        ])

    CALC_OPSKPCHK = [
        (lambda v: v == 0, None),
        (lambda v: v == 1, lambda v: v == 0),
        (lambda v: v != 0, None),
    ]

    locals().update(d
        for sym, (name, opnum, *_) in CALC_OPDESC.items()
        for d in [(
            f'_gen_anode_act_calc_{name}',
            (lambda dsym: (
                lambda self, nd, ctx, **ka:
                self._gen_vnode_act_calc_2(dsym, *nd.subs, ctx, **ka)
            ) if opnum == 2 else (
                lambda self, nd, ctx, **ka:
                self._gen_vnode_act_calc_1(dsym, *nd.subs, ctx, **ka)
            ))(sym)
        )])

    def _gen_vnode_act_calc_1(self, op, nd, ctx, *,
            prv_oplvl = 0, prv_opdir = 0, calc_value = None, **ka):
        oplvl = self.CALC_OPLVL[op]
        op = op[:-1]
        needb = (prv_oplvl == oplvl and prv_opdir == 0 or prv_oplvl > oplvl)
        if needb:
            ctx['buf'].write('(')
        ctx['buf'].write(op)
        opdv_cntn = [None]
        self._gen_optkargs_anode(self._getone(nd), None, ctx,
            prv_oplvl = oplvl, prv_opdir = 1, calc_value = opdv_cntn)
        opdv = opdv_cntn[0]
        if needb:
            ctx['buf'].write(')')
        if calc_value and not opdv is None:
            calc_value[0] = eval(f'{op}{opdv}')

    def _gen_vnode_act_calc_2(self, op, nd1, nd2, ctx, *,
            prv_oplvl = 0, prv_opdir = 0, calc_value = None, **ka):
        oplvl = self.CALC_OPLVL[op]
        skplvl, skptyp = self.CALC_OPDESC[op][2:4]
        pyop = {'&&': ' and ', '||': ' or '}.get(op, op)
        needb = (prv_oplvl == oplvl and prv_opdir == 1 or prv_oplvl > oplvl)
        pbuf = ctx['buf']
        sbuf1 = ctx['buf'] = pbuf.sub_inline()
        opdv = []
        opdv_cntn = [None]
        self._gen_optkargs_anode(self._getone(nd1), None, ctx,
            prv_oplvl = oplvl, prv_opdir = 0, calc_value = opdv_cntn)
        opdv.append(opdv_cntn[0])
        sbuf2 = ctx['buf'] = pbuf.sub_inline()
        opdv_cntn = [None]
        self._gen_optkargs_anode(self._getone(nd2), None, ctx,
            prv_oplvl = oplvl, prv_opdir = 1, calc_value = opdv_cntn)
        opdv.append(opdv_cntn[0])
        skpopd = None
        hasval = True
        for i, v in enumerate(opdv):
            if v is None:
                hasval = False
                continue
            chkskp, chkerr = self.CALC_OPSKPCHK[skptyp[i]]
            if chkerr and chkerr(v):
                self._error(nd, f'invalid value {i}: {v}')
            if chkskp(v):
                if skplvl[i] > 1:
                    skpopd = 1 - i # another opd
                    break
                elif skplvl[i] > 0:
                    skpopd = i
        if not self.conf.get('reduce_calc'):
            skpopd = None
        if skpopd is None:
            if needb:
                pbuf.write('(')
        if skpopd != 0:
            sbuf1.touch()
        if skpopd is None:
            pbuf.write(f' {op} ')
        if skpopd != 1:
            sbuf2.touch()
        if skpopd is None:
            if needb:
                pbuf.write(')')
        if calc_value and hasval:
            calc_value[0] = eval(f'{opdv[0]}{pyop}{opdv[1]}')
        ctx['buf'] = pbuf

    # ref

    def _gen_anode_ref_func(self, nd, ctx):
        ctx['buf'].write(str(nd))

    def _gen_anode_ref_label(self, nd, ctx):
        ctx['buf'].write(str(nd))

    def _gen_anode_parm(self, nd, ctx):
        ctx['buf'].write(str(nd))

    def _gen_anode_inst(self, nd, ctx, *, calc_value = None, **ka):
        val = nd.val
        if val & 0x4000000:
            val -= 0x8000000
        if calc_value:
            calc_value[0] = val
        ctx['buf'].write(hex(val))

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
            cd = c_scode_program(ast, c_scode_buf_null())
            #cd = c_scode_program(ast, c_scode_buf_std())
            cd.gen_code()
        else:
            with open(r'wktab\output.txt', 'w', encoding = 'utf-8') as fd:
                cd = c_scode_program(ast, c_scode_buf_fd(fd))
                cd.gen_code()
    tst1()
