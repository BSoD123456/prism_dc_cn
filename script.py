#! python3
# coding: utf-8

from sect import *
from report import report

@tabkey('command')
class c_script_file(c_sect_tab):
    _TAB_WIDTH = 4
    @tabitm()
    def get_command(self, ofs):
        val = self.U32(ofs)
        return val >> 0x1b, val & 0x7ffffff

class c_script_anode:
    pass

class c_script_anode_inst(c_script_anode):

    def __init__(self, val):
        self.val = val

    def __repr__(self):
        return hex(self.val)[2:] if isinstance(self.val, int) else str(self.val)

class c_script_anode_arg(c_script_anode):

    def __init__(self, aidx):
        self.aidx = aidx

    def __repr__(self):
        return f'arg{self.aidx}'

class c_script_anode_act(c_script_anode):

    def __init__(self, name, args, addr):
        self.name = name
        self.subs = args
        self.addr = addr

    def __repr__(self):
        sr = ', '.join(repr(n) for n in self.subs)
        return f'{self.name}({sr})'

class c_script_anode_act_ret(c_script_anode_act):
    pass

class c_script_anode_act_none(c_script_anode_act):
    pass

class c_script_anode_bat:

    def __init__(self, acts):
        self.subs = acts

    def rebalance(self, par):
        nsubs = self.subs
        self.subs = [nsubs.pop()]
        par.extend(nsubs)

    def _repr_as(self, flat):
        if flat:
            return '\n'.join(f'{n.addr:x}: {n}' for n in self.subs)
        else:
            return '|'.join(repr(n) for n in self.subs)

    def __repr__(self):
        return self._repr_as(False)

class c_script_anode_func:

    def __init__(self, name, args, rets, bat):
        self.name = name
        self.args = args
        self.rets = rets
        self.sub = bat

    def __repr__(self):
        ar = ', '.join(self.args)
        rr = ', '.join(self.rets)
        sr = self.sub._repr_as(True)
        return f'{self.name} ({ar}) -> {rr}:\n{sr}'

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
            0x14: (None, 1, 0, 'jmp'),
            0x15: ('if', 2, 0, 'bra'),
            0x16: ('if_not', 2, 0, 'bra'),
        }),
        ('call', 0, 1, 0, 'call'),
        ('syscall', 0, 1, 0, 'call'),
        ('return', 0, 0, 0, 'ret'),
        ('txtcall', 0, 1, 0, 'call'),
        ('halloc', 1, 0, 0),
        ('hfree', 1, 0, 0),
        ('hpush', 0, 0, 1),
        # 0x10
        ('pass', 0, 0, 0),
        ('text', {
            '__par__': (None, 0, 0),
            0x3ffffff: ('end', 0, 0, 'ret'),
        }),
        ('texth', 1, 0, 0),
    ]

    _SYS_FUNC = [
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
    ]

    def __init__(self, sect):
        self.sect = sect
        self.wkset = set()

    def _error(self, addr, msg):
        report('err', f'(addr:{addr:x}) {msg}')
        raise ValueError(msg)

    @staticmethod
    def _keyget(o, k, d = None):
        try:
            return o[k]
        except (KeyError, IndexError, TypeError):
            return d

    @staticmethod
    def make_anode_act(name, args, rnum, ctype, addr):
        if rnum:
            assert rnum == 1
            return c_script_anode_act_ret(name, args, addr)
        else:
            return c_script_anode_act_none(name, args, addr)

    def _rdcmd(self, addr):
        self.wkset.add(addr)
        return self.sect[addr]

    def _walked(self, addr):
        return addr in self.wkset

    def _getsysfunc(self, addr):
        return self._keyget(self._SYS_FUNC, addr)

    def _getfunc(self, functab, addr):
        #return fname, anum, rnum
        return f'f_{addr:x}', 0, 1

    def _getinst(self, bat, removable):
        assert isinstance(bat, c_script_anode_bat)
        if not (removable and len(bat.subs) == 1
                or not removable and len(bat.subs) > 0):
            return None
        act = bat.subs[-1]
        if not (act and act.name == 'push'):
            return None
        inst = act.subs[0]
        if not isinstance(inst, c_script_anode_inst):
            return None
        return inst.val

    def _parse_func(self, addr, functab):
        branches = []
        msneed = 0
        bra, msneed = self._parse_func_bra(addr, functab, msneed, branches)
        return bra

    def _parse_func_bra(self, staddr, functab, msneed, branches):
        cmd_list = self._CMD_INFO
        mstack = []
        cur_bat_cntn = [[]]
        def bpush(nd):
            cur_bat_cntn[0].append(nd)
        def mpop(rb):
            if len(mstack) < 1:
                msneed += 1
                return c_script_anode_arg(msneed)
            nd = mstack.pop()
            if rb:
                nd.rebalance(cur_bat_cntn[0])
            return nd
        def mpush(nd):
            mstack.append(nd)
        def mpushb():
            mpush(c_script_anode_bat(cur_bat_cntn[0]))
            cur_bat_cntn[0] = []
        addr = staddr
        while True:
            cmd, parm = self._rdcmd(addr)
            
            cinfo = self._keyget(cmd_list, cmd)
            if not cinfo:
                self._error(addr, f'invalid cmd: {cmd:x}')
            if isinstance(cinfo[1], int):
                cname, pnum, snum, rnum = cinfo[:4]
                ctype = self._keyget(cinfo, 4, 'std')
            else:
                cname, sub_list = cinfo
                cinfo = self._keyget(sub_list, parm)
                if not cinfo:
                    cinfo = self._keyget(sub_list, '__par__')
                    if not cinfo:
                        self._error(addr, f'invalid sub-cmd: {cmd:x} {parm:x}')
                    pnum = 1
                else:
                    pnum = 0
                sname, snum, rnum = cinfo[:3]
                ctype = self._keyget(cinfo, 3, 'std')
                if sname:
                    cname = '_'.join((cname, sname))

            if ctype == 'call':
                assert snum > 0
                cdst_nd = mpop(True)
                cdst = self._getinst(cdst_nd, True)
                if not cdst:
                    self._error(addr, f'call to non-instant addr: {cdst_nd}')
                snum -= 1
                if cname == 'syscall':
                    finfo = self._getsysfunc(cdst)
                else:
                    finfo = self._getfunc(functab, cdst)
                if finfo is None:
                    self._error(addr, f'unreachable call: {cname} {cdst:x}')
                fname, fanum, frnum = finfo
                cname = '_'.join((cname, fname))
                snum += fanum
                rnum += frnum
            
            assert pnum < 2
            cargs = []
            for i in range(snum):
                cargs.append(mpop(i == snum - 1))
            if pnum:
                cargs.append(c_script_anode_inst(parm))
            cargs.reverse()
            
            anode = self.make_anode_act(cname, cargs, rnum, ctype, addr)
            #print(f'{addr:x}: {anode}')
            bpush(anode)
            if isinstance(anode, c_script_anode_act_ret):
                mpushb()

            if ctype == 'jmp':
                adst = self._getinst(cargs[0], False)
                if not adst:
                    self._error(addr, f'jump to non-instant addr: {cargs[0]}')
                if self._walked(adst):
                    break
                addr = adst
            elif ctype == 'ret':
                break
            else:
                addr += 1

        if len(mstack) > 0:
            self._error(staddr, f'branch main stack unbalance: {len(mstack)}')
        mpushb()
        return mstack.pop(), msneed

    def parse_sect(self):
        return self._parse_func(0, {})
            
if __name__ == '__main__':
    import pdb
    from hexdump import hexdump as hd
    from pprint import pprint
    ppr = lambda *a, **ka: pprint(*a, **ka, sort_dicts = False)

    def tst1():
        global sc, prog, ast
        with open(r'wktab\SCRIPT.BIN', 'rb') as fd:
            raw = fd.read()
        sc = c_script_file(raw, 0)
        sc.parse_size(len(raw), 4)
        prog = c_script_program(sc)
        ast = prog.parse_sect()
        #for i in ast:
        #    print('===')
        #    print(i._repr_as(True))
        print(ast._repr_as(True))
    tst1()
