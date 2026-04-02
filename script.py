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
        ('push', 1, 0, 1),
        ('pop', 0, 1, 0),
        ('calc', [
            # 0x0
            (None, 0, 0),
            ('add', 2, 1),
            ('sub', 2, 1),
            ('mul', 2, 1),
            ('div', 2, 1),
            ('mod', 2, 1),
            ('neg', 1, 1),
            ('eq', 2, 1),
            # 0x8
            ('gt', 2, 1),
            ('ge', 2, 1),
            ('lt', 2, 1),
            ('le', 2, 1),
            ('ne', 2, 1),
            ('and', 2, 1),
            ('or', 2, 1),
            ('band', 2, 1),
            # 0x10
            ('bor', 2, 1),
            ('bxor', 2, 1),
            ('shl', 2, 1),
            ('shr', 2, 1),
        ]),
        # 0x8
        ('jump', {
            0x14: (None, 1, 0),
            0x15: ('when', 2, 0),
            0x16: ('when_not', 2, 0),
        }),
        ('call', 0, 1, 0),
        ('syscall', [
            # 0x0
            ('0', 1, 1),
            ('1', 1, 1),
            ('2', 1, 1),
            ('3', 0, 1),
            ('4_i1', 0, 1),
            ('5_e', 0, 1),
            ('6_c', 0, 0),
            ('7_c', 0, 0),
            # 0x8
            ('8_c', 0, 0),
            ('9', 0, 1),
            ('a', 0, 1),
            ('b', 1, 1),
            ('c_n1i2ni34n5i', 3, 1), #0:peek2;pop1;peek2;pop1;pop1;->n1->i2|i3 / 2->n4|i3|n3 / 3:push1;->r / 4:call d27;->n5:pop1->i2
            ('d_n1i2ni34n5i', 3, 1), #0:peek2;pop1;peek2;pop1;pop1;->n1->i2|i3 / 2->n3|i3|i4 / 3:push1->r / 4:call d27;->n5:pop1->i2
            ('e_i2', 0, 1),
            ('f_c', 0, 0),
            # 0x10
            ('10', 1, 1),
            ('11_c', 0, 0),
            ('12_c', 0, 0),
            ('13_c', 0, 0),
            ('14_c', 0, 0),
            ('15_c', 0, 0),
            ('16', 1, 1),
            ('17', 1, 1),
            # 0x18
            ('18', 2, 1),
            ('19', 1, 1),
            ('1a', 0, 1),
            ('1b', 1, 1),
            ('1c_c', 0, 0),
            ('1d', 4, 1),
            ('1e', 1, 1),
            ('1f', 1, 1),
            # 0x20
            ('20', 0, 1),
            ('21_n1', 1, 1), # pop1;push1;call 1f9b; -> 1:pop1;push1;
            ('22', 2, 1),
            ('23', 0, 1),
            ('24', 1, 1),
            ('25', 1, 1),
            ('26', 3, 1),
            ('27', 1, 1),
            # 0x28
            ('28', 1, 1),
            ('29', 0, 1),
            ('2a', 1, 1),
            ('2b', 0, 1),
            ('2c', 0, 1),
            ('2d', 0, 1),
            ('2e', 0, 1),
            ('2f', 0, 1),
            # 0x30
            ('30', 0, 1),
            ('31', 1, 1),
            ('32', 2, 1),
            ('33_i3e', 1, 1),
            ('34_i3e', 1, 1),
            ('35', 1, 1),
            ('36', 1, 1),
        ]),
        ('return', 0, 0, 0),
        ('txtcall', 0, 1, 0),
        ('halloc', 1, 0, 0),
        ('hfree', 1, 0, 0),
        ('hpush', 0, 0, 1),
        # 0x10
        ('pass', 0, 0, 0),
        ('text', 2, 0, 0),
        ('texth', 2, 0, 0),
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
