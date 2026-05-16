#! python3
# coding: utf-8

from scode import with_anode, c_scode_parser
from report import report

@with_anode('prim')
class c_semit_program(c_scode_parser):

    def __init__(self, ast, buf, conf = None):
        dconf = {}
        if conf:
            dconf = {**dconf, **conf}
        super().__init__(ast, buf, dconf)

    

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
    from scode import c_scode_buf_null, c_scode_buf_std, c_scode_buf_fd
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
                cd = c_semit_program(ast, c_scode_buf_fd(fd))
                cd.gen_code()
    tst1()
