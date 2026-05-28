#! python3
# coding: utf-8

from charset import _get_gbk_char_type

import re

def read_chars(fd):
    rcs = []
    while True:
        line = fd.readline()
        if not line:
            break
        for c in line.strip():
            if not c in rcs:
                rcs.append(c)
    return rcs

def modzh_ipt(sfd, dfd, mfd, rplc):
    seltab = {}
    tabidx = 0
    lstintab = False
    sln = 0
    patt = r'(?<![^\x00-\x7f])([^\x00-\x7f])(?![^\x00-\x7f])'
    while True:
        sln += 1
        sline = sfd.readline()
        dline = dfd.readline()
        if not sline:
            assert not dline
            break
        assert dline
        if sln < 57090 or dline == '\n':
            mfd.write(dline)
            continue
        sseq = re.split(patt, sline)
        dseq = re.split(patt, dline)
        if not len(sseq) == len(dseq):
            raise ValueError(f'unmatched line: {dline}')
        mseq = []
        selidx = None
        for i, (sv, dv) in enumerate(zip(sseq, dseq)):
            if i % 2 == 0:
                mseq.append(dv)
                m = re.match(r'.*\[SEL\:([0-9a-fA-F])+\]', sv)
                if m:
                    selidx = int(m.group(1), 16)
            else:
                if isinstance(selidx, int):
                    if sv in seltab:
                        raise ValueError(f'duplicate char: {sv}')
                    mchar = '？'
                    if tabidx in rplc:
                        cs = rplc[tabidx]
                        if cs:
                            mchar = cs.pop(0)
                    seltab[sv] = (selidx, tabidx, mchar)
                else:
                    if not sv in seltab:
                        raise ValueError(f'unref char: {sv}')
                    mchar = seltab[sv][-1]
                    selidx = False
                mseq.append(mchar)
        if selidx is False:
            if lstintab:
                tabidx += 1
            lstintab = False
        elif not selidx is None:
            lstintab = True
        mfd.write(''.join(mseq))
    if any(len(cs) > 0 for cs in rplc.values()):
        raise ValueError(f'unfinished replace chars: {rplc}')
    return seltab, tabidx

if __name__ == '__main__':
    import pdb
    from hexdump import hexdump as hd
    from pprint import pprint
    ppr = lambda *a, **ka: pprint(*a, **ka, sort_dicts = False)

    def main():
        global cs, st, rcs
        rplc = {}
        with open(r'trans\selfvocate.txt', 'r', encoding = 'utf-8') as fd:
            rcs = read_chars(fd)
        rplc[16] = rcs.copy()
        with open(r'trans\origname.txt', 'r', encoding = 'utf-8') as fd:
            rcs = read_chars(fd)
        rplc[36] = rcs.copy()
        with open(r'wktab_bak\dialog_done2.txt', 'r', encoding = 'utf-8') as sfd:
            #with open(r'trans\dialog_zh.txt', 'r', encoding = 'utf-8') as dfd:
            with open(r'wktab_bak\dialog_done2.txt', 'r', encoding = 'utf-8') as dfd:
                with open(r'trans\dialog_zh_mod_ipt.txt', 'w', encoding = 'utf-8') as mfd:
                    st, tn = modzh_ipt(sfd, dfd, mfd, rplc)
        cs = []
        cdmin = float('inf')
        cdi = None
        for i in range(tn):
            scs = [c for c, (_, t, v) in st.items() if t == i]
            cs.append(scs)
            cd = len(scs) - len(rcs)
            if 0 <= cd < cdmin:
                cdmin = cd
                cdi = i
        print(f'most matched: {cdi}')
    main()
