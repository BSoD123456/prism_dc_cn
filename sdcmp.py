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

    def _feed_shdw(self, ln, shd_dlg):
        shd_seq = []
        for i, s in enumerate(re.split(r'\<tr\: ([t0-9a-z]+)\>', shd_dlg)):
            if i % 2 == 0:
                if not s or s == '\n':
                    continue
                m = re.match(r'\{([^\{\}]+)\}', s)
                if not m:
                    self._error(ln, f'unknown text in shadow: {s}')
                shd_seq.append(m.group(1))
            else:
                shd_seq.append(s)
        return shd_seq

    def _feed_line(self, ln, src_dlg, dst_dlg, shd_dlg):
        if src_dlg == shd_dlg:
            if dst_dlg != shd_dlg:
                self._error(ln, 'unmatched lines')
            return
        shd_seq = self._feed_shdw(ln, shd_dlg)
        self.linebuf[ln] = (src_dlg, dst_dlg, shd_seq)

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
