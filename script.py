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

class c_script_anode_parm(c_script_anode_leaf):

    def __init__(self, aidx):
        self.aidx = aidx

    def __repr__(self):
        return f'arg{self.aidx}'

class c_script_anode_ref(c_script_anode_leaf):

    def __init__(self, name, addr):
        self.name = name
        self.addr = addr

class c_script_anode_ref_func(c_script_anode_ref):

    def __repr__(self):
        return f'&fun.{self.name}'

class c_script_anode_ref_label(c_script_anode_ref):

    def __repr__(self):
        return f'&lab.{self.name}'

class c_script_anode_label(c_script_anode_leaf):

    def __init__(self, name, addr):
        self.name = name
        self.addr = addr

    def __repr__(self):
        return f'@lab.{self.name}:'

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

# bat := [act | label]
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

    def _repr_as(self, form):
        if form == 'tab':
            return '\n'.join(f'{n.addr:x}: {n}' for n in self.subs)
        elif form == 'func':
            return '\n'.join(repr(n) for n in self.subs)
        else:
            return '|'.join(repr(n) for n in self.subs)

    def __repr__(self):
        return self._repr_as(None)

class c_script_anode_func(c_script_anode_branch):

    def __init__(self, name, anum, rnum, bat, addr):
        self.name = name
        self.anum = anum
        self.rnum = rnum
        self.sub = bat
        self.addr = addr

    def _repr_as(self, form):
        ar = ', '.join(f'arg{i+1}' for i in range(self.anum))
        if form == 'tab':
            rr = ', '.join(f'ret{i+1}' for i in range(self.rnum))
            sr = self.sub._repr_as('tab')
            return f'{self.addr:x}: func {self.name}({ar}) -> {rr} {{\n{sr}\n}}'
        else:
            sr = self.sub._repr_as('func')
            return f'func {self.name}({ar}){{\n{sr}\n}}'

    def __repr__(self):
        return self._repr_as(None)

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
        ('6_c', 4, 1),
        ('7_c', 0, 1),
        # 0x8
        ('8_c', 1, 1),
        ('9', 0, 1),
        ('a', 0, 1),
        ('b', 1, 1),
        ('c_n1i2ni34n5i', 3, 1), #0:peek2;pop1;peek2;pop1;pop1;->n1->i2|i3 / 2->n4|i3|n3 / 3:push1;->r / 4:call d27;->n5:pop1->i2
        ('d_n1i2ni34n5i', 3, 1), #0:peek2;pop1;peek2;pop1;pop1;->n1->i2|i3 / 2->n3|i3|i4 / 3:push1->r / 4:call d27;->n5:pop1->i2
        ('e_i2', 0, 1),
        ('f_c', 1, 1),
        # 0x10
        ('10', 1, 1),
        ('11_c', 1, 1),
        ('12_c', 1, 1),
        ('13_c', 1, 1),
        ('14_c', 1, 1),
        ('15_c', 1, 1),
        ('16', 1, 1),
        ('17', 1, 1),
        # 0x18
        ('18', 2, 1),
        ('19', 1, 1),
        ('1a', 0, 1),
        ('1b', 1, 1),
        ('1c_c', 1, 1),
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
        return self.sect[addr]

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

    def _parse_func(self, fname, staddr, functab, funcdecs, gwkset, cpath):
        assert not staddr in functab
        if fname in cpath:
            return 'recursed'
        cpath.append(fname)
        
        fwkset = set()
        labtab = {}
        braseq = [(None, staddr, 0)]
        branches = []
        unfinshed = False
        msinfo = None
        while braseq:
            lname, addr, msneed = braseq.pop()
            if addr in labtab:
                continue
            labtab[addr] = c_script_anode_label(lname, addr) if lname else None
            #print('===', lname, hex(addr))
            bra, bmsinfo = self._parse_func_bra(
                addr, functab, funcdecs, msneed, braseq, fwkset, gwkset, cpath.copy())
            if bra == 'recursed':
                unfinshed = True
                continue
            gwkset.update(fwkset)
            if not bmsinfo is None:
                if msinfo is None:
                    msinfo = bmsinfo
                elif msinfo != bmsinfo:
                    self._error(addr,
                        f'different numbers of func stack: {msinfo} -> {bmsinfo}')
            if len(bra.subs) > 0:
                branches.append(bra)
                #print(bra._repr_as(True))

        if msinfo is None:
            self._error(staddr, f'function no return: {fname} @ {staddr:x}')
        functab[staddr] = (fname, *msinfo)
        if unfinshed:
            return 'unfinished'
        
        lbbat = c_script_anode_bat([
            n for a, n in sorted(labtab.items(), key = lambda v: v[0])
            if n])
        branches.insert(0, lbbat)
        func = c_script_anode_func(
            fname,
            *msinfo,
            self._merge_bra(branches),
            staddr)
        funcdecs[staddr] = func
        return 'done'

    def _parse_func_bra(self,
            staddr, functab, funcdecs, msneed, braseq, fwkset, gwkset, cpath):
        cmd_list = self._CMD_INFO
        mstack = []
        msneed_cntn = [msneed]
        msinfo = None
        cur_bat_cntn = [[]]
        def bpush(nd):
            cur_bat_cntn[0].append(nd)
        def mpop(nb):
            if len(mstack) < 1:
                msneed_cntn[0] += 1
                return c_script_anode_parm(msneed_cntn[0])
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

        addr = staddr
        while True:
            
            if addr in fwkset:
                mcheck(addr)
                break
            elif addr in gwkset:
                self._error(addr, f'function codes should be isolated')
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
                if cdst is None:
                    self._error(addr, f'call to non-instant addr: {cdst_nd}')
                if ctype == 'call':
                    if cname == 'syscall':
                        finfo = self._keyget(self._SYS_FUNC, cdst)
                    else:
                        if not cdst in functab:
                            fname =  f'{cdst:x}'
                            fsta = self._parse_func(
                                fname, cdst, functab, funcdecs, gwkset, cpath)
                            if fsta == 'recursed':
                                return fsta, None
                        finfo = functab[cdst]
                    if finfo is None:
                        self._error(addr, f'unreachable call: {cname} {cdst:x}')
                    dname, dsnum, drnum = finfo
                    if rbed and dsnum > 0:
                        self._error(addr, f'should not rebalance after args: {cdst_nd}')
                    if cname == 'syscall':
                        dname = f's{dname}'
                    lb = c_script_anode_ref_func(dname, cdst)
                    snum += dsnum
                    rnum += drnum
                else:
                    lb = c_script_anode_ref_label(f'{cdst:x}', cdst)
                mpush(c_script_anode_bat([lb]))
            elif ctype == 'ret':
                msret = len(mstack)
                snum += msret
            
            assert pnum < 2
            cargs = []
            for i in range(snum):
                cargs.append(mpop(i < snum - 1))
            if pnum:
                cargs.append(c_script_anode_inst(parm))
            cargs.reverse()
            
            anode = self.make_anode_act(cname, cargs, rnum, ctype, addr)
            bpush(anode)
            if rnum > 0:
                mpushb()
            #if len(mstack) == 0: print(f'{addr:x}: {anode}')

            if ctype in ['jmp', 'bra']:
                adst = self._getbtail(cargs[-1], False)
                if not isinstance(adst, c_script_anode_ref_label):
                    self._error(addr, f'jump to non-instant addr: {cargs[-1]}')
                if ctype == 'jmp':
                    addr = adst.addr
                else:
                    mcheck(addr)
                    braseq.append((adst.name, adst.addr, msneed_cntn[0]))
                    addr += 1
            elif ctype == 'ret':
                mcheck(addr)
                msinfo = (msneed_cntn[0], msret)
                break
            else:
                addr += 1

        mpushb()
        return mstack.pop(), msinfo

    def _merge_bra(self, branches):
        minaddrs = [b.subs[0].addr if b.subs else None for b in branches]
        raseq = []
        while True:
            mna = INF
            mni = None
            for i, m in enumerate(minaddrs):
                if not m is None and m < mna:
                    mna = m
                    mni = i
            if mni is None:
                break
            ds = branches[mni].subs
            raseq.append(ds.pop(0))
            minaddrs[mni] = ds[0].addr if ds else None
        return c_script_anode_bat(raseq)

    def parse_sect(self):
        gwkset = set()
        cpath = []
        funcs = {}
        self._parse_func('main', 0, {}, funcs, gwkset, cpath)
        return funcs
            
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
        print(ast)
    tst1()
