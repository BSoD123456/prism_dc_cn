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

class c_script_anode_prog(c_script_anode_bat):

    def __repr__(self):
        return self._repr_as('func')

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

    def _warn(self, addr, msg):
        report('war', f'(addr:{addr:x}) {msg}')

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

    def _getlabname(self, addr):
        return f'{addr:x}'

    def _getfuncname(self, addr):
        return f'{addr:x}'

    def _parse_func(self, staddr, functab, gwkset):
        progctx = {}
        sustab = {}
        braseq = [(staddr, staddr, 0)]
        faddr = None

        while True:
            while braseq:

                nfaddr, addr, msneed = braseq.pop()
                if nfaddr != faddr:
                    faddr = nfaddr
                    if not faddr in progctx:
                        progctx[faddr] = {
                            'fwkset': set(),
                            'labset': set(),
                            'bralst': [],
                        }
                    fwkset = progctx[faddr]['fwkset']
                    labset = progctx[faddr]['labset']
                    bralst = progctx[faddr]['bralst']

                bwkset = fwkset.copy()
                bra, blabs, bsta, binfo = self._parse_func_bra(
                    addr, functab, msneed, bwkset, gwkset)
                #print('lab', blabs)
                for a, m in blabs:
                    if a in labset:
                        continue
                    labset.add(a)
                    braseq.append((faddr, a, m))
                if bra:
                    if len(bra.subs) > 0:
                        bralst.append(bra)
                    progctx[faddr]['fwkset'] = fwkset = bwkset
                    gwkset.update(fwkset)
                    if bsta == 'return':
                        #print('ret', faddr, addr, binfo)
                        if not faddr in functab:
                            functab[faddr] = binfo
                            if faddr in sustab:
                                susseq = sustab.pop(faddr)
                                #print('append', faddr, susseq)
                                for v in susseq.values():
                                    braseq.append(v)
                        elif functab[faddr] != binfo:
                            self._error(addr,
                                f'different numbers of func stack: {functab[faddr]} -> {binfo}')
                else:
                    if bsta == 'call':
                        #print('sus', binfo, faddr, addr)
                        if not binfo in sustab:
                            sustab[binfo] = {}
                        if not addr in sustab[binfo]:
                            sustab[binfo][addr] = (faddr, addr, msneed)
                        elif sustab[binfo][addr] != (faddr, addr, msneed):
                            self._error(addr,
                                f'conflicting suspend info: {(faddr, addr, msneed)} / {sustab[binfo][addr]}')

            if not sustab:
                break
            for a in sustab:
                braseq.append((a, a, 0))
                sustab[a] = sustab.pop(a)
                break

        return progctx

    def _parse_func_bra(self,
            staddr, functab, msneed, fwkset, gwkset):
        cmd_list = self._CMD_INFO
        labseq = []
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
        def bpack():
            nd = c_script_anode_bat(cur_bat_cntn[0])
            cur_bat_cntn[0] = []
            return nd
        def mpushb():
            mpush(bpack())
        def mcheck(a):
            if len(mstack) > 0:
                self._error(a, f'branch main stack unbalance: {len(mstack)}')

        addr = staddr
        while True:
            
            if addr in fwkset:
                mcheck(addr)
                return bpack(), labseq, 'part', None
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
                            return None, labseq, 'call', cdst
                        finfo = (
                            self._getfuncname(cdst), *functab[cdst])
                    if finfo is None:
                        self._error(addr, f'unreachable call: {cname} {cdst:x}')
                    dname, dsnum, drnum = finfo
                    if rbed and (dsnum > 0 and len(mstack) > 0):
                        self._error(addr,
                            f'should not rebalance after args: {cdst_nd}')
                    if cname == 'syscall':
                        dname = f's{dname}'
                    lb = c_script_anode_ref_func(dname, cdst)
                    snum += dsnum
                    rnum += drnum
                else:
                    lb = c_script_anode_ref_label(
                        self._getlabname(cdst), cdst)
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
                    labseq.append((adst.addr, msneed_cntn[0]))
                    addr += 1
            elif ctype == 'ret':
                mcheck(addr)
                return bpack(), labseq, 'return', (msneed_cntn[0], msret)
            else:
                addr += 1

        assert False

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

    def _post_parse_prog(self, functab, progctxs):
        progbat = []
        fawkset = set()
        for progctx in progctxs:
            for faddr, ctx in progctx.items():
                if faddr in fawkset:
                    self._warn(faddr,
                        f'ignore duplicated function: {self._getfuncname(faddr)}')
                    continue
                fawkset.add(faddr)
                lbbat = c_script_anode_bat([
                    c_script_anode_label(
                        self._getlabname(a), a)
                    for a in sorted(ctx['labset'])
                    if a != faddr])
                bralst = [lbbat]
                bralst.extend(ctx['bralst'])
                func = c_script_anode_func(
                    self._getfuncname(faddr),
                    *functab[faddr],
                    self._merge_bra(bralst),
                    faddr)
                progbat.append(func)
        progbat.sort(key = lambda nd: nd.addr)
        prog = c_script_anode_prog(progbat)
        return prog

    def parse_sect(self):
        gwkset = set()
        functab = {}
        progctx = self._parse_func(0, functab, gwkset)
        prog = self._post_parse_prog(functab, [progctx])
        return prog
            
if __name__ == '__main__':
    import pdb
    from hexdump import hexdump as hd
    from pprint import pprint
    ppr = lambda *a, **ka: pprint(*a, **ka, sort_dicts = False)

    def tst1():
        global sc, prog, ast
        fn = r'wktab\SCRIPT.BIN'
        #fn = r'wktab\tst_recur1.bin'
        with open(fn, 'rb') as fd:
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
