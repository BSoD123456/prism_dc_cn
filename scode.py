#! python3
# coding: utf-8

from charset import c_charset_jp
from report import report

class err_scode_syntax(ValueError):
    pass

class c_scode_buf:

    IDTSYM = '    '

    def __init__(self, parent, touched):
        self.par = parent
        self.tch = touched
        self.idt = 0
        self.lbuf = []
        self.buf = []

    def indent(self, val):
        self.idt += val
        if self.idt < 0:
            raise err_scode_syntax('indent underflow')

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
        self._writeline(''.join((*self._idtsym(), *self.lbuf)))
        self.lbuf = []

    def touch(self):
        if self.tch:
            return
        for line in self.buf:
            self._write_par(line)

class c_scode_buf_std(c_scode_buf):

    def __init__(self):
        super().__init__(None, True)

    def _writeline(self, line):
        print(line)

class c_scode_program:

    def __init__(self, ast, buf):
        self.ast = ast
        self.buf = buf
        self.chrset = c_charset_jp()

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
        ctx['text'] = {}
        for snd in nd.subs:
            self._gen_anode(snd, 'dectext', ctx)

    def _gen_anode_func_dectext(self, nd, ctx):
        pass

    def _gen_anode_text_dectext(self, nd, ctx):
        txts = []
        for c in nd.text:
            txts.append(self.chrset.dec(c))
        txt = ''.join(txts)
        self.buf.write(f'{nd.name}: {txt}')
        self.buf.newline()

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
