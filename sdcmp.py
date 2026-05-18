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
        txt_seq = []
        tmpl_seq = []
        for i, s in enumerate(re.split(r'\{([^\{\}]+)\}', dlg)):
            if i % 2 == 0:
                if i == 1 and not s:
                    continue
                elif s.endswith('\n'):
                    s = s[:-1]
                    if not s:
                        continue
                txt_seq.append(s)
            else:
                tmpl_seq.append(s)
        return txt_seq, tuple(tmpl_seq)

    def _feed_shdw(self, ln, shd_seq):
        for i in range(len(shd_seq)):
            s = shd_seq[i]
            seq = []
            for j, trs in enumerate(re.split(r'\<t(?:r\:\s*([t0-9a-z\/]+)|d)\>', s)):
                if j % 2 == 0:
                    if trs:
                        self._error(ln, f'unknown text in shadow: {trs}')
                else:
                    if trs:
                        if '/' in trs:
                            self._error(ln, f'multiline textref unsupported: {trs}')
                        if trs in self.txttab:
                            self._error(ln, f'duplicated textref: {trs}')
                        self.txttab[trs] = [ln]
                    else:
                        trs = 'EOL'
                    seq.append(trs)
            shd_seq[i] = seq

    def _feed_line(self, ln, src_dlg, dst_dlg, shd_dlg):
        if src_dlg == shd_dlg:
            if dst_dlg != shd_dlg:
                self._error(ln, 'unmatched line')
            return
        src_seq, src_tmpl_seq = self._split_tmpl(src_dlg)
        dst_seq, dst_tmpl_seq = self._split_tmpl(dst_dlg)
        shd_seq, shd_tmpl_seq = self._split_tmpl(shd_dlg)
        if not src_tmpl_seq == shd_tmpl_seq:
            self._error(ln, f'unmatched line')
        if not dst_tmpl_seq == shd_tmpl_seq:
            self._error(ln, f'shaffled trans: {dst_tmpl_seq}')
        self._feed_shdw(ln, shd_seq)
        if not len(src_seq) == len(shd_seq):
            self._error(ln, f'unmatched line')
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
    tst1()
