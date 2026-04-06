#! python3
# coding: utf-8

from charset import c_charset_jp
from report import report

class err_scode_syntax(ValueError):
    pass

class c_scode_program:

    def __init__(self, ast):
        self.ast = ast
        self.chrset = c_charset_jp()

    def parse(self):
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
    def tst1():
        global ast, code
        ast = loadobj(r'wktab\ast.pck')
        code = c_scode_program(ast)
    tst1()
