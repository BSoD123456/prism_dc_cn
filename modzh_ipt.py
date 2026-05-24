#! python3
# coding: utf-8

from charset import _get_gbk_char_type

import re

def modzh(sfd, dfd, mfd):
    sln = 0
    while True:
        sln += 1
        sline = sfd.readline()
        dline = dfd.readline()
        if sln < 57090:
            mfd.write(dline)
            continue
        

if __name__ == '__main__':
    import pdb
    from hexdump import hexdump as hd
    from pprint import pprint
    ppr = lambda *a, **ka: pprint(*a, **ka, sort_dicts = False)

    def main():
        with open(r'wktab\dialog_done2.txt', 'r', encoding = 'utf-8') as dfd:
            with open(r'trans\dialog_zh.txt', 'r', encoding = 'utf-8') as dfd:
                with open(r'trans\dialog_zh_mod_ipt.txt', 'w', encoding = 'utf-8') as mfd:
                    modzh(sfd, dfd)
    #main()
