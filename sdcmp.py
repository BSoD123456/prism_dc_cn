#! python3
# coding: utf-8

from report import report

import re

class c_sdialog_comparer:

    def __init__(self):
        self.txttab = {}
        self.linebuf = {}

    def _error(self, ln, msg):
        report('err', f'(ln: {ln}) {msg}')
        raise ValueError(msg)

    def _warn(self, ln, msg):
        report('war', f'(ln: {ln}) {msg}')

    def _split_tmpl(self, dlg):
        seq = []
        for i, s in enumerate(re.split(r'\{([^\{\}]+)\}', dlg)):
            if i % 2 == 0:
                if not s:
                    continue
                elif s.endswith('\n'):
                    s = s[:-1]
                typ = 'txt'
            else:
                typ = 'tmpl'
            seq.append((typ, s))
        return seq

    def _feed_shdw(self, ln, shd_seq):
        seq = []
        for typ, s in shd_seq:
            if typ != 'txt':
                seq.append((typ, s))
                continue
            for i, trs in enumerate(re.split(r'\<tr\: ([t0-9a-z]+)\>', s)):
                if i % 2 == 0:
                    if trs:
                        self._error(ln, f'unknown text in shadow: {trs}')
                else:
                    seq.append(('tref', trs))
                    if trs in self.txttab:
                        rinfo = self.txttab[trs]
                    else:
                        rinfo = self.txttab[trs] = [[]]
                    rinfo[0].append(ln)
        return seq

    def _feed_line(self, ln, src_dlg, dst_dlg, shd_dlg):
        if src_dlg == shd_dlg:
            if dst_dlg != shd_dlg:
                self._error(ln, 'unmatched lines')
            return
        src_seq = self._split_tmpl(src_dlg)
        dst_seq = self._split_tmpl(dst_dlg)
        shd_seq = self._feed_shdw(ln, self._split_tmpl(shd_dlg))
        self.linebuf[ln] = (src_seq, dst_seq, shd_seq)

    def feed(self, srcfd, dstfd, shdfd):
        ln = 0
        while True:
            ln += 1
            s = srcfd.readline()
            d = dstfd.readline()
            h = shdfd.readline()
            if not s:
                if d or h:
                    self._error(ln, 'unmatched lines number')
                break
            self._feed_line(ln, s, d, h)

    def scan(self):
        pass

if __name__ == '__main__':
    import pdb
    from hexdump import hexdump as hd
    from pprint import pprint
    ppr = lambda *a, **ka: pprint(*a, **ka, sort_dicts = False)

    def tst1():
        global cmp
        cmp = c_sdialog_comparer()
        print('start')
        with open(r'wktab\dialog_trim.txt', 'r', encoding = 'utf-8') as srcfd:
            with open(r'trans\dialog_trim_zh.txt', 'r', encoding = 'utf-8') as dstfd:
                with open(r'wktab\dialog_trim.shadow.txt', 'r', encoding = 'utf-8') as shdfd:
                    cmp.feed(srcfd, dstfd, shdfd)
        cmp.scan()
    tst1()
