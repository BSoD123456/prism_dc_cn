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

    def newline(self, idt = 0):
        if self.lbuf:
            line = ''.join((*self._idtsym(), *self.lbuf))
            self.lbuf = []
        else:
            line = ''
        self._writeline(line)
        if idt:
            self.indent(idt)

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

class c_scode_program:

    def __init__(self, ast, buf):
        self.ast = ast
        self.buf = buf
        self.chrset = c_charset_jp()

    def _error(self, nd, msg):
        report('err', f'(addr:{nd.addr:x}) {msg}')
        raise err_scode_syntax(msg)

    def _warn(self, nd, msg):
        report('war', f'(addr:{nd.addr:x}) {msg}')

    def _gen_anode(self, nd, assume = None, ctx = None):
        cn = nd.__class__.__name__
        assert cn.startswith('c_script_anode_')
        cn = '_gen_anode_' + cn[len('c_script_anode_'):]
        if hasattr(nd, 'name'):
            mn = '_'.join(
                (cn, nd.name, assume) if assume else (cn, nd.name))
            if hasattr(self, mn):
                return getattr(self, mn)(nd, ctx)
        if assume:
            mn = '_'.join((cn, assume))
        else:
            mn = cn
        return getattr(self, mn)(nd, ctx)

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

    def _gen_anode_func_dectext(self, nd, ctx):
        pass

    def _gen_anode_text_dectext(self, nd, ctx):
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
        pbuf.write(f'{nd.repr_as("proto")} {{')
        pbuf.newline()
        buf = ctx['buf'] = pbuf.sub()
        self._gen_anode(nd.sub, None, ctx)
        buf.touch()
        ctx['buf'] = pbuf
        pbuf.write('}')
        pbuf.newline()
        return 'func'

    def _gen_anode_text(self, nd, ctx):
        pass

    def _gen_anode_bat(self, nd, ctx):
        for snd in nd.subs:
            self._gen_anode(snd, None, ctx)

    def _gen_anode_label(self, nd, ctx):
        oidt = ctx['buf'].popindent()
        ctx['buf'].write(str(nd))
        ctx['buf'].newline()
        ctx['buf'].indent(oidt)

    def _gen_anode_act(self, nd, ctx):
        ctx['buf'].write(str(nd))
        ctx['buf'].newline()

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
        cd = c_scode_program(ast, c_scode_buf_std())
        cd.gen_code()
    tst1()
