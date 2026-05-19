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

class c_script_anode_act_call(c_script_anode_act):
    pass

# bat := [act | label]
class c_script_anode_bat(c_script_anode_branch):

    def __init__(self, acts):
        self.subs = acts

    def repr_as(self, form):
        if form == 'tab':
            return '\n'.join(f'{n.addr:x}: {n}' for n in self.subs)
        elif form == 'func':
            return '\n'.join(repr(n) for n in self.subs)
        else:
            return '|'.join(repr(n) for n in self.subs)

    def __repr__(self):
        return self.repr_as(None)

class c_script_anode_prog(c_script_anode_bat):

    def __repr__(self):
        return self.repr_as('func')

class c_script_anode_func(c_script_anode_branch):

    def __init__(self, name, anum, rnum, bat, addr):
        self.name = name
        self.anum = anum
        self.rnum = rnum
        self.sub = bat
        self.addr = addr

    def repr_as(self, form):
        ar = ', '.join(f'arg{i+1}' for i in range(self.anum))
        prt = f'fun.{self.name}({ar})'
        if self.rnum > 0:
            rr = ', '.join(f'ret' for i in range(self.rnum))
            prt = ' '.join((rr, prt))
        if form == 'proto':
            return prt
        elif form == 'tab':
            sr = self.sub.repr_as('tab')
            return f'{self.addr:x}: {prt} {{\n{sr}\n}}'
        else:
            sr = self.sub.repr_as('func')
            return f'{prt}{{\n{sr}\n}}'

    def __repr__(self):
        return self.repr_as(None)

class c_script_anode_text(c_script_anode_func):

    def __init__(self, name, text, addr):
        self.name = name
        self.text = text
        self.addr = addr

    def __repr__(self):
        return f'txt.{self.name}:{self.text}'

class c_script_anode_pad(c_script_anode_func):

    def __init__(self, plen, addr):
        self.addr = addr
        self.plen = plen

    def __repr__(self):
        return f'pad.{{self.addr:x}}_{self.plen:x}'

SC_CMD_INFO = [
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

SC_SYS_FUNC = [
    # 0x0
    ('set_name', 1, 1),
    ('get_name', 1, 1),
    ('get_ctrl', 1, 1),
    ('3', 0, 1),
    ('4_i1', 0, 1), #i1
    ('5_e', 0, 1), #e
    ('6_c', 4, 1), #c
    ('7_c', 0, 1), #c
    # 0x8
    ('8_c', 1, 1), #c
    ('9', 0, 1),
    ('a', 0, 1),
    ('b', 1, 1),
    ('print_text', 3, 1), #0:peek2;pop1;peek2;pop1;pop1;->n1->i2|i3 / 2->n4|i3|n3 / 3:push1;->r / 4:call d27;->n5:pop1->i2
    ('print_text_choose', 3, 1), #0:peek2;pop1;peek2;pop1;pop1;->n1->i2|i3 / 2->n3|i3|i4 / 3:push1->r / 4:call d27;->n5:pop1->i2
    ('print_text_continue', 0, 1), #i2
    ('f_c', 1, 1),
    # 0x10
    ('10', 1, 1),
    ('11_c', 1, 1), #c
    ('set_bg', 1, 1), #c
    ('set_char', 1, 1), #c
    ('14_c', 1, 1), #c
    ('set_icon', 1, 1), #c
    ('16', 1, 1),
    ('17', 1, 1),
    # 0x18
    ('18', 2, 1),
    ('19', 1, 1),
    ('1a', 0, 1),
    ('1b', 1, 1),
    ('1c_c', 1, 1), #c
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
    ('33_i3e', 1, 1), #i3e
    ('34_i3e', 1, 1), #i3e
    ('35', 1, 1),
    ('36', 1, 1),
]

class c_script_program:

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
        if ctype == 'call':
            return c_script_anode_act_call(name, args, rnum, addr)
        else:
            return c_script_anode_act(name, args, rnum, addr)

    def _rdcmd(self, addr):
        return self.sect[addr]

    def _getbhead(self, bat):
        if len(bat.subs) < 1:
            return None
        return bat.subs[0]

    def _rplcbhead(self, bat, nd):
        bat.subs[0] = nd
        return bat

    def _getainst(self, bat):
        if not (isinstance(bat, c_script_anode_bat) and len(bat.subs) == 1):
            return None
        inst = bat.subs[0]
        if not isinstance(inst, c_script_anode_inst):
            return None
        return inst.val

    def _getinst(self, bat):
        act = self._getbhead(bat)
        if not (act and act.name == 'push'):
            return None
        return self._getainst(act.subs[0])

    def _getlabname(self, addr):
        return f'{addr:x}'

    def _getfuncname(self, addr):
        return f'{addr:x}'

    def _gettxtname(self, addr):
        return f't{addr:x}'

    def _parse_text(self, bat):
        txt = []
        for i, nd in enumerate(bat.subs):
            if not (isinstance(nd, c_script_anode_act)
                    and nd.name.startswith('text')):
                self._error(addr,
                    f'text func should not have non-text act: {nd}')
            if nd.name in ('text', 'texth'):
                assert len(nd.subs) == 1
                val = self._getainst(nd.subs[0])
                assert val and (val & 0x3ffffff) != 0x3ffffff
                v1 = val & 0x1fff
                if nd.name == 'texth':
                    v1 |= 0x2000
                txt.append(v1)
                v2 = ((val >> 0xd) & 0x1fff)
                if v2 != 0x1fff:
                    if nd.name == 'texth':
                        v2 |= 0x2000
                    txt.append(v2)
            elif not (nd.name == 'text_end' and i == len(bat.subs) - 1):
                self._error(addr,
                    f'invalid text act: {nd}')
        return txt

    @staticmethod
    def _scan_hole(wkset, faddr, labset, braseq):
        for i in range(min(wkset), max(wkset) + 1):
            if not i in wkset and i - 1 in wkset:
                labset.add(i)
                braseq.append((
                    i if faddr is None else faddr,
                    i, [[]], None))

    def _parse_func(self, staddr, functab, gwkset):
        progctx = {}
        sustab = {}
        suswkset = set()
        braseq = [(staddr, staddr, [[]], 0)]
        faddr = None

        while True:
            while braseq:

                nfaddr, addr, mstack, msneed = braseq.pop()
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

                bra, blabs, bsta, binfo = self._parse_func_bra(
                    addr, functab, mstack, msneed, fwkset, gwkset)
                gwkset.update(fwkset)
                #print('lab', blabs)
                for a, m, prs in blabs:
                    if a in labset:
                        continue
                    labset.add(a)
                    if prs:
                        braseq.append((faddr, a, [[]], m))
                if bra:
                    if len(bra.subs) > 0:
                        bralst.append(bra)
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
                        caddr, csaddr, cmstack, cmsneed = binfo
                        if not caddr in sustab:
                            sustab[caddr] = {}
                        if not csaddr in sustab[caddr]:
                            sustab[caddr][csaddr] = (faddr, csaddr, cmstack, cmsneed)
                        else:
                            sfaddr, scsaddr, scmstack, scmsneed = sustab[caddr][csaddr]
                            if (
                                    sfaddr, scsaddr, len(scmstack), scmsneed
                                ) != (
                                    faddr, csaddr, len(cmstack), cmsneed):
                                self._error(csaddr,
                                    f'conflicting suspend info: {faddr, csaddr, len(cmstack), cmsneed} / {(sfaddr, scsaddr, len(scmstack), scmsneed)}')

            if not sustab:
                for fa, fc in progctx.items():
                    fw = fc['fwkset']
                    lbs = fc['labset']
                    self._scan_hole(fw, fa, lbs, braseq)
                if not braseq:
                    break
                continue
            susstep = tuple(k for s in sustab.values() for k in s)
            if susstep in suswkset:
                self._error(susstep[0], 'recursed invoke')
            suswkset.add(susstep)
            for a in sustab:
                braseq.append((a, a, [[]], 0))
                sustab[a] = sustab.pop(a)
                break

        return progctx

    def _parse_func_bra(self,
            staddr, functab, mstack, msneed, fwkset, gwkset):
        cmd_list = SC_CMD_INFO
        labseq = []
        msneed_cntn = [msneed]
        def bpush(nd):
            mstack[-1].append(nd)
        def bextend(bat):
            mstack[-1].extend(bat.subs)
        def mpush():
            mstack.append([])
        def mpop():
            if len(mstack) < 2:
                assert len(mstack) == 1
                if msneed is None:
                    self._error(staddr, f'hole mstack underflow')
                msneed_cntn[0] += 1
                b = [c_script_anode_parm(msneed_cntn[0])]
            else:
                b = mstack.pop()
            nd = c_script_anode_bat(b)
            return nd
        def mcheck(a, ret):
            mdeep = len(mstack) - 1
            if mdeep != 0:
                if msneed is None:
                    # flush for holes
                    rbat = mstack[0]
                    for bat in mstack[1:]:
                        mstack.pop() # mstack[1:] cached, not mstack, so you can do this
                        rbat.extend(bat)
                else:
                    self._error(a, f'branch main stack unbalance: {mdeep}')
            if ret:
                return c_script_anode_bat(mstack.pop())

        def mrestruct_for_return():
            rbat = mstack[0]
            ridx = 0
            for bat in mstack[1:]:
                mstack.pop() # mstack[1:] cached, not mstack, so you can do this
                nd = bat[0]
                rsnd = c_script_anode_act('setrval', [
                    c_script_anode_bat([c_script_anode_inst(ridx)]),
                    c_script_anode_bat([nd])
                ], 0, nd.addr)
                ridx += 1
                rbat.append(rsnd)
                for nd in bat[1:]:
                    rbat.append(nd)
            mpush()
            bpush(c_script_anode_inst(ridx))
            return ridx

        addr = staddr
        while True:
            
            if addr in fwkset:
                return mcheck(addr, True), labseq, 'part', None
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
                cdst_nd = mpop()
                cdst = self._getinst(cdst_nd)
                if cdst is None:
                    self._error(addr, f'call to non-instant addr: {cdst_nd}')
                if ctype == 'call':
                    if cname == 'syscall':
                        finfo = self._keyget(SC_SYS_FUNC, cdst)
                        if finfo is None:
                            self._error(addr,
                                f'unreachable call: {cname} {cdst:x}')
                        dname, dsnum, drnum = finfo
                        dname = f'{dname}'
                    else:
                        if not cdst in functab:
                            mpush()
                            bextend(cdst_nd)
                            fwkset.remove(addr)
                            return None, labseq, 'call', (
                                cdst, addr, mstack, msneed_cntn[0])
                        dsnum, drnum, dcname = functab[cdst]
                        if dcname == 'text_end':
                            dname = self._gettxtname(cdst)
                        else:
                            dname = self._getfuncname(cdst)
                    lb = c_script_anode_ref_func(dname, cdst)
                    snum += dsnum
                    rnum += drnum
                else:
                    lb = c_script_anode_ref_label(
                        self._getlabname(cdst), cdst)
                mpush()
                bextend(self._rplcbhead(cdst_nd, lb))
            elif ctype == 'ret':
                msret = mrestruct_for_return()
                assert snum == pnum == 0
                snum = 1
            
            assert pnum < 2
            cargs = []
            for _ in range(snum):
                cargs.append(mpop())
            if pnum:
                cargs.append(c_script_anode_bat([c_script_anode_inst(parm)]))
            cargs.reverse()
            
            anode = self.make_anode_act(cname, cargs, rnum, ctype, addr)
            if rnum > 0:
                mpush()
            bpush(anode)
            #if len(mstack) == 0: print(f'{addr:x}: {anode}')

            if ctype in ['jmp', 'bra']:
                adst = self._getbhead(cargs[-1])
                if not isinstance(adst, c_script_anode_ref_label):
                    self._error(addr, f'jump to non-instant addr: {cargs[-1]}')
                if ctype == 'jmp':
                    labseq.append((adst.addr, msneed_cntn[0], False))
                    addr = adst.addr
                else:
                    mcheck(addr, False)
                    labseq.append((adst.addr, msneed_cntn[0], True))
                    addr += 1
            elif ctype == 'ret':
                return mcheck(addr, True), labseq, 'return', (
                    msneed_cntn[0], msret, cname)
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
        progbot = {}
        for progctx in progctxs:
            for faddr, ctx in progctx.items():
                if faddr in fawkset:
                    self._warn(faddr,
                        f'ignore duplicated function: {self._getfuncname(faddr)}')
                    continue
                fawkset.add(faddr)
                if not faddr in functab:
                    self._error(faddr,
                        f'function without return: {self._getfuncname(faddr)}')
                lbbat = c_script_anode_bat([
                    c_script_anode_label(
                        self._getlabname(a), a)
                    for a in sorted(ctx['labset'])
                    if a != faddr])
                bralst = [lbbat]
                bralst.extend(ctx['bralst'])
                fanum, frnum, fcname = functab[faddr]
                fbat = self._merge_bra(bralst)
                if fcname == 'text_end':
                    txt = self._parse_text(fbat)
                    func = c_script_anode_text(
                        self._gettxtname(faddr),
                        txt,
                        faddr)
                else:
                    func = c_script_anode_func(
                        self._getfuncname(faddr),
                        fanum, frnum,
                        fbat,
                        faddr)
                progbat.append(func)
                progbot[faddr] = max(ctx['fwkset']) + 1
        padding_progbat = []
        last_bot = 0
        for func in sorted(progbat, key = lambda nd: nd.addr):
            faddr = func.addr
            plen = faddr - last_bot
            if plen != 0:
                assert plen > 0
                self._warn(last_bot, f'padding 0x{plen:x}: {last_bot:x} - {last_bot+plen:x}')
                padding_progbat.append(c_script_anode_pad(plen, last_bot))
            padding_progbat.append(func)
            last_bot = progbot[faddr]
        prog = c_script_anode_prog(padding_progbat)
        return prog

    def parse_sect(self, entry):
        gwkset = set()
        functab = {}
        progctx = self._parse_func(entry, functab, gwkset)
        prog = self._post_parse_prog(functab, [progctx])
        return prog

if __name__ == '__main__':
    import pdb
    from hexdump import hexdump as hd
    from pprint import pprint
    ppr = lambda *a, **ka: pprint(*a, **ka, sort_dicts = False)

    import pickle
    def saveobj(o, n):
        with open(n, 'wb') as fd:
            pickle.dump(o, fd)

    def tst1():
        global sc, prog, ast
        fn = r'wktab\SCRIPT.BIN'
        #fn = r'wktab\escript_mod.bin'
        #fn = r'wktab\tst_recur1.bin'
        #fn = r'wktab\tst_noret.bin'
        with open(fn, 'rb') as fd:
            raw = fd.read()
        sc = c_script_file(raw, 0)
        sc.parse_size(len(raw), 4)
        prog = c_script_program(sc)
        ast = prog.parse_sect(0)
        #for k, i in ast.items():
        #    print('===', k)
        #    print(i.repr_as(True))
        #print(ast.repr_as(True))
        #print(ast)
        saveobj(ast, r'wktab\ast.pck')
        #saveobj(ast, r'wktab\ast_mod.pck')
    tst1()
