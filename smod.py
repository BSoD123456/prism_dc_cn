#! python3
# coding: utf-8

from scode import with_anode, c_scode_parser

@with_anode()
class c_smod_program(c_scode_parser):

    def __init__(self, ast, conf = None):
        dconf = {}
        if conf:
            dconf = {**dconf, **conf}
        super().__init__(ast, dconf)

    # program

    def _gen_anode_prog(self, nd, ctx):
        for snd in nd.subs:
            self._gen_anode(snd, None, ctx)

    def _gen_anode_pad(self, nd, ctx):
        pass

    def _gen_anode_func(self, nd, ctx):
        pass

    def _gen_anode_text(self, nd, ctx):
        pass

    # intf

    def mod_text(self, rtxt):
        ctx = {}
        ctx['rplc_text'] = rtxt
        self._gen_anode(self.ast)
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
    def tst1():
        global ast, cd
        ast = loadobj(r'wktab\ast.pck')
        print('start')
        cd = c_smod_program(ast)
        rtxt = cmp_sdialog(r'wktab\dialog_trim.txt', r'trans\dialog_trim_zh.txt', r'wktab\dialog_trim.shadow.txt')
        mast = cd.mod_text(rtxt)
    tst1()
