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

class err_script_syntax(ValueError):
    pass

class c_script_anode:
    pass

class c_script_anode_leaf(c_script_anode):
    pass

class c_script_anode_branch(c_script_anode):
    pass

class c_script_anode_inst(c_script_anode_leaf):

    def __init__(self, val):
        self.val = val

    def __repr__(self):
        return hex(self.val)[2:] if isinstance(self.val, int) else str(self.val)

class c_script_anode_arg(c_script_anode_leaf):

    def __init__(self, aidx):
        self.aidx = aidx

    def __repr__(self):
        return f'arg{self.aidx}'

class c_script_anode_label(c_script_anode_leaf):

    def __init__(self, name, addr):
        self.name = name
        self.addr = addr

class c_script_anode_label_func(c_script_anode_label):

    def __repr__(self):
        return f'@fun_{self.name}'

class c_script_anode_label_bat(c_script_anode_label):

    def __repr__(self):
        return f'@lab_{self.name}'

class c_script_anode_act(c_script_anode_branch):

    def __init__(self, name, args, rnum, addr):
        self.name = name
        self.subs = args
        self.rnum = rnum
        self.addr = addr

    def _repr_args(self):
        return ', '.join(repr(n) for n in self.subs)

    def __repr__(self):
        sr = self._repr_args()
        return f'{self.name}({sr})'

class c_script_anode_bat(c_script_anode_branch):

    def __init__(self, acts):
        self.subs = acts

    def rebalance(self, par):
        nsubs = self.subs
        rbed = (len(nsubs) > 1)
        if rbed:
            self.subs = [nsubs.pop()]
            par.extend(nsubs)
        return rbed

    def _repr_as(self, flat):
        if flat:
            return '\n'.join(f'{n.addr:x}: {n}' for n in self.subs)
        else:
            return '|'.join(repr(n) for n in self.subs)

    def __repr__(self):
        return self._repr_as(False)

class c_script_anode_func(c_script_anode_branch):

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
        raise err_script_syntax(msg)

    @staticmethod
    def _keyget(o, k, d = None):
        try:
            return o[k]
        except (KeyError, IndexError, TypeError):
            return d

    @staticmethod
    def make_anode_act(name, args, rnum, ctype, addr):
        assert rnum < 2
        return c_script_anode_act(name, args, rnum, addr)

    def _rdcmd(self, addr):
        self.wkset.add(addr)
        return self.sect[addr]

    def _walked(self, addr):
        return addr in self.wkset

    def _getsysfunc(self, addr):
        n, s, r = self._keyget(self._SYS_FUNC, addr)
        return f's{n}', s, r

    def _getfunc(self, functab, addr):
        #return fname, anum, rnum
        return f'{addr:x}', 0, 1

    def _getbtail(self, bat, removable):
        assert isinstance(bat, c_script_anode_bat)
        if not (removable and len(bat.subs) == 1
                or not removable and len(bat.subs) > 0):
            return None
        return bat.subs[-1]

    def _getinst(self, bat, removable):
        act = self._getbtail(bat, removable)
        if not (act and act.name == 'push'):
            return None
        inst = act.subs[0]
        if not isinstance(inst, c_script_anode_inst):
            return None
        return inst.val

    def _parse_func(self, staddr, functab):
        fwkset = set()
        labtab = {}
        braseq = [('entry', staddr)]
        msneed = 0
        branches = {}
        while braseq:
            lname, addr = braseq.pop()
            bra, msneed = self._parse_func_bra(addr, functab, labtab, msneed, braseq, fwkset)
            branches[lname] = bra
            print('===', lname)
            print(bra._repr_as(True))
        return branches

    def _parse_func_bra(self, staddr, functab, labtab, msneed, braseq, fwkset):
        cmd_list = self._CMD_INFO
        mstack = []
        cur_bat_cntn = [[]]
        def bpush(nd):
            cur_bat_cntn[0].append(nd)
        def mpop(nb):
            if len(mstack) < 1:
                msneed += 1
                return c_script_anode_arg(msneed)
            nd = mstack.pop()
            if not nb:
                rbed = nd.rebalance(cur_bat_cntn[0])
                if nb is None:
                    return nd, rbed
            return nd
        def mpush(nd):
            mstack.append(nd)
        def mpushb():
            mpush(c_script_anode_bat(cur_bat_cntn[0]))
            cur_bat_cntn[0] = []
        def mcheck(a):
            if len(mstack) > 0:
                self._error(a, f'branch main stack unbalance: {len(mstack)}')
        def walked(a):
            if self._walked(a):
                if not a in fwkset:
                    self._error(a, f'function codes should be isolated')
                return True
            else:
                return False
        addr = staddr
        while True:
            if walked(addr):
                mcheck(addr)
                break
            cmd, parm = self._rdcmd(addr)
            fwkset.add(addr)
            
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

            if ctype in ('call', 'jmp', 'bra'):
                assert snum > 0
                cdst_nd, rbed = mpop(None)
                cdst = self._getinst(cdst_nd, True)
                if not cdst:
                    self._error(addr, f'call to non-instant addr: {cdst_nd}')
                if ctype == 'call':
                    if cname == 'syscall':
                        finfo = self._getsysfunc(cdst)
                    else:
                        finfo = self._getfunc(functab, cdst)
                    if finfo is None:
                        self._error(addr, f'unreachable call: {cname} {cdst:x}')
                    dname, dsnum, drnum = finfo
                    if rbed and dsnum > 0:
                        self._error(addr, f'should not rebalance after args: {cdst_nd}')
                    lb = c_script_anode_label_func(dname, cdst)
                    snum += dsnum
                    rnum += drnum
                else:
                    lb = c_script_anode_label_bat(f'{cdst:x}', cdst)
                mpush(c_script_anode_bat([lb]))
            
            assert pnum < 2
            cargs = []
            for i in range(snum):
                cargs.append(mpop(i < snum - 1))
            if pnum:
                cargs.append(c_script_anode_inst(parm))
            cargs.reverse()
            
            anode = self.make_anode_act(cname, cargs, rnum, ctype, addr)
            #print(f'{addr:x}: {anode}')
            bpush(anode)
            if rnum > 0:
                mpushb()

            if ctype in ['jmp', 'bra']:
                mcheck(addr)
                adst = self._getbtail(cargs[-1], False)
                if not isinstance(adst, c_script_anode_label_bat):
                    self._error(addr, f'jump to non-instant addr: {cargs[-1]}')
                if ctype == 'jmp':
                    addr = adst.addr
                else:
                    if not adst in labtab:
                        braseq.append((adst.name, adst.addr))
                    addr += 1
            elif ctype == 'ret':
                mcheck(addr)
                break
            else:
                addr += 1

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
        #for k, i in ast.items():
        #    print('===', k)
        #    print(i._repr_as(True))
        #print(ast._repr_as(True))
    tst1()
