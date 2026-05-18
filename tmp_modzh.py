#! python3
# coding: utf-8

def modzh(sfd, dfd, mfd):
    sline = sfd.readline()
    dline = dfd.readline()
    while sline:
        if dline == '\n' and sline != '\n':
            dline = dfd.readline()
            continue
        mfd.write(dline)
        sline = sfd.readline()
        dline = dfd.readline()

if __name__ == '__main__':
    import pdb
    from hexdump import hexdump as hd
    from pprint import pprint
    ppr = lambda *a, **ka: pprint(*a, **ka, sort_dicts = False)

    def main():
        with open(r'wktab\dialog_trim.txt', 'r', encoding = 'utf-8') as sfd:
            with open(r'trans\dialog_trim_zh.txt', 'r', encoding = 'utf-8') as dfd:
                with open(r'trans\dialog_trim_zh_mod.txt', 'w', encoding = 'utf-8') as mfd:
                    modzh(sfd, dfd, mfd)
    main()
