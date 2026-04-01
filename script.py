#! python3
# coding: utf-8

from sect import *

@tabkey('command')
class c_script_file(c_sect_tab):
    _TAB_WIDTH = 4
    @tabitm()
    def get_command(self, ofs):
        val = self.U32(ofs)
        return val >> 0x1b, val & 0x7ffffff

class c_script_program:

    _CMD_INFO = [
        # 0x0
        ('nop', 0, 0, 0),
        ('vset', 0, 2, 1),
        ('vmask', 0, 2, 1),
        ('vget', 0, 1, 1),
        ('vcheck', 0, 1, 1),
        ('push', 1, 1, 0),
        ('pop', 0, 0, 1),
        ('calc', 1, None, 1),
        # 0x8
        ('jump', 1, None, None),
        ('call', 0, None, None),
        ('syscall', 0, None, None),
        ('return', 0, None, None),
        ('txtcall', 0, None, None),
        ('halloc', 1, 0, 0),
        ('hfree', 1, 0, 0),
        ('hpush', 0, 1, 0),
        # 0x10
        ('pass', 0, 0, 0),
        ('text', 2, None, None),
        ('texth', 2, None, None),
    ]

    def __init__(self, sect):
        self.sect = sect

if __name__ == '__main__':
    import pdb
    from hexdump import hexdump as hd
    from pprint import pprint
    ppr = lambda *a, **ka: pprint(*a, **ka, sort_dicts = False)

    def tst1():
        global sc
        with open(r'wktab\SCRIPT.BIN', 'rb') as fd:
            raw = fd.read()
        sc = c_script_file(raw, 0)
        sc.parse_size(len(raw), 4)
    tst1()
