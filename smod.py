#! python3
# coding: utf-8

from scode import with_anode, c_scode_parser
from charset import c_charset_zh, c_charset_jp

@with_anode()
class c_smod_program(c_scode_parser):

    def __init__(self, ast, conf = None):
        dconf = {}
        if conf:
            dconf = {**dconf, **conf}
        super().__init__(ast, dconf)
        self.chrset = c_charset_zh()
        #self.chrset = c_charset_jp()

    def _encode_text(self, txt):
        return self.chrset.encode(txt.replace('\n', '[LF]'))

    # program

    def _gen_anode_prog(self, nd, ctx):
        for snd in nd.subs:
            self._gen_anode(snd, None, ctx)

    def _gen_anode_pad(self, nd, ctx):
        pass

    def _gen_anode_func(self, nd, ctx):
        pass

    def _gen_anode_text(self, nd, ctx):
        dtxt = ctx['rplc_text'].get(nd.name, None)
        if dtxt is None:
            pass#self._warn(nd, f'unmod text: {nd.name}')
        else:
            nd.text = self._encode_text(dtxt)

    # intf

    def modify(self, rtxt):
        ctx = {}
        ctx['rplc_text'] = rtxt
        self._gen_anode(self.ast, None, ctx)
        return self.ast

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
    from sdcmp import cmp_sdialog
    from scode import c_scode_buf_fd
    from semit import c_semit_program, c_semit_asm_buf_fd
    from fonmkr import make_font_hzk
    def tst1():
        global ast, cd
        ast = loadobj(r'wktab\ast.pck')
        print('start')
        cd = c_smod_program(ast)
        print('cmp')
        rtxt = cmp_sdialog(
            r'wktab\dialog_trim.txt',
            #r'wktab\dialog_trim.txt',
            r'trans\dialog_trim_zh.txt',
            r'wktab\dialog_trim.shadow.txt')
        print('mod')
        mast = cd.modify(rtxt)
        print('emit')
        conf = {
            'entries': SC_PROG_ENTRY,
            'padding': False }
        if 0:
            with open(r'wktab\escript_mod.txt', 'w', encoding = 'utf-8') as fd:
                emt = c_semit_program(mast, c_scode_buf_fd(fd), conf)
                emt.gen_code()
        else:
            with open(r'wktab\escript_mod.bin', 'wb') as fd:
                emt = c_semit_program(mast, c_semit_asm_buf_fd(fd), conf)
                emt.gen_code()
        print('font')
        dfon = make_font_hzk(
            r'wktab\FONT.DAT', r'wktab\HZK24S', cd.chrset.ext_chars)
        with open(r'wktab\font_mod.dat', 'wb') as fd:
            fd.write(dfon.BYTES())
    tst1()
