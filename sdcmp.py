#! python3
# coding: utf-8

from report import report

import re

class c_sdialog_comparer:

    def __init__(self):
        self.trefwk = {}
        self.treftxt = {}
        self.rmtref = []

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
                txt_seq.append(s)
            else:
                tmpl_seq.append(s)
        return txt_seq, tuple(tmpl_seq)

    def _split_shdw(self, ln, shd_seq):
        for i in range(len(shd_seq)):
            s = shd_seq[i]
            seq = []
            for j, trs in enumerate(re.split(r'\<t(?:r\:\s*([t0-9a-z\/]+)|d)\>', s)):
                if j % 2 == 0:
                    if not trs or trs == '\n':
                        continue
                    self._error(ln, f'unknown text in shadow: {trs}')
                else:
                    if trs:
                        if '/' in trs:
                            self._error(ln, f'multiline textref unsupported: {trs}')
                        if trs in self.trefwk:
                            self._error(ln, f'duplicated textref: {trs}')
                        self.trefwk[trs] = ln
                    else:
                        trs = '__EOL__'
                    seq.append(trs)
            shd_seq[i] = seq

    def _tgrp_tail(self, tgrp):
        ti = len(tgrp) - 1
        teol = False
        if ti >= 0:
            if tgrp[ti] != '__EOL__':
                return ti, teol
            teol = True
            ti -= 1
        if ti >= 0:
            assert teol
            return ti, teol
        return None, teol

    def _tgrp_match_txt(self, ln, tgrp, txt):
        tti, teol = self._tgrp_tail(tgrp)
        if txt.endswith('\n'):
            if teol:
                txt = txt[:-1]
        elif teol:
            self._error(ln, 'unmatched EOL')
        return tti, txt

    def _treftab_bind_txt(self, ln, txt, tgrp):
        treftxt = self.treftxt
        rmtref = self.rmtref
        tti, txt = self._tgrp_match_txt(ln, tgrp, txt)
        if tti is None:
            if not txt:
                return
            if not rmtref:
                self._error(ln, 'textref not enough')
            trs = rmtref.pop()
        else:
            trs = tgrp[tti]
            rmtref.extend(tgrp[:tti])
        assert not trs in treftxt
        treftxt[trs] = txt

    def _treftab_flush(self):
        treftxt = self.treftxt
        rmtref = self.rmtref
        for trs in rmtref:
            assert not trs in treftxt
            treftxt[trs] = ''

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
        self._split_shdw(ln, shd_seq)
        assert len(src_seq) == len(dst_seq) == len(shd_seq)
        seqlen = len(src_seq)
        for i in range(seqlen):
            src_txt = src_seq[i]
            dst_txt = dst_seq[i]
            shd_grp = shd_seq[i]
            smtti, smtxt = self._tgrp_match_txt(ln, shd_grp, src_txt)
            if smtxt and smtti is None:
                self._error(ln, f'unmatched textref')
            self._treftab_bind_txt(ln, dst_txt, shd_grp)

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
        self._treftab_flush()

def cmp_sdialog(srcfn, dstfn, shdfn):
    cmp = c_sdialog_comparer()
    with open(srcfn, 'r', encoding = 'utf-8') as srcfd:
        with open(dstfn, 'r', encoding = 'utf-8') as dstfd:
            with open(shdfn, 'r', encoding = 'utf-8') as shdfd:
                cmp.feed(srcfd, dstfd, shdfd)
    return cmp.treftxt

if __name__ == '__main__':
    import pdb
    from hexdump import hexdump as hd
    from pprint import pprint
    ppr = lambda *a, **ka: pprint(*a, **ka, sort_dicts = False)

    def tst1():
        global rtxt, rtref, rtitm
        print('start')
        rtxt = cmp_sdialog(r'wktab\dialog_trim.txt', r'trans\dialog_trim_zh.txt', r'wktab\dialog_trim.shadow.txt')
        rtref = [*rtxt.keys()]
        rtitm = [*rtxt.items()]
    tst1()
