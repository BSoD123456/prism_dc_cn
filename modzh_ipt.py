#! python3
# coding: utf-8

from charset import _get_gbk_char_type

import re

def modzh(sfd, dfd, mfd):
    sln = 0
    patt = r'(?<![^\x00-\x7f])([^\x00-\x7f])(?![^\x00-\x7f])'
    while True:
        sln += 1
        sline = sfd.readline()
        dline = dfd.readline()
        if not sline:
            assert not dline
            break
        if sln < 57090:
            mfd.write(dline)
            continue
        sseq = re.split(patt, sline)
        dseq = re.split(patt, dline)
        if not len(sseq) == len(dseq):
            raise ValueError(f'unmatched line: {dline}')
        mseq = []
        for i, (sv, dv) in enumerate(zip(sseq, dseq)):
            if i % 2 == 0:
                mseq.append(dv)
            else:
                if sv != dv:
                    raise ValueError(f'unmatched key char: {sv}/{dv}')
                mseq.append('？')
        mfd.write(''.join(mseq))

if __name__ == '__main__':
    import pdb
    from hexdump import hexdump as hd
    from pprint import pprint
    ppr = lambda *a, **ka: pprint(*a, **ka, sort_dicts = False)

    def main():
        with open(r'wktab\dialog_done2.txt', 'r', encoding = 'utf-8') as sfd:
            with open(r'trans\dialog_zh.txt', 'r', encoding = 'utf-8') as dfd:
                with open(r'trans\dialog_zh_mod_ipt.txt', 'w', encoding = 'utf-8') as mfd:
                    modzh(sfd, dfd, mfd)
    main()
