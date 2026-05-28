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
            self._error(ln, f'textref not enough for {txt}')
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
            return None
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
        return shd_seq

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

    def feed_lines(self, srclines, dstlines, shdlines):
        if not len(srclines) == len(dstlines) == len(shdlines):
            self._error(0, 'unmatched lines number')
        for i in range(len(srclines)):
            s = srclines[i]
            d = dstlines[i]
            h = shdlines[i]
            self._feed_line(i+1, s, d, h)
        self._treftab_flush()

    def result(self):
        return self.treftxt

class c_sdialog_comparer_check(c_sdialog_comparer):

    def __init__(self):
        super().__init__()
        self._chk_cnt_tab = []
        self._chk_fnd_tab = {}

    def _feed_line(self, ln, src_dlg, dst_dlg, shd_dlg):
        shd_seq = super()._feed_line(ln, src_dlg, dst_dlg, shd_dlg)
        if not shd_seq is None:
            self._check_dialog(
                ln, dst_dlg, src_dlg, shd_seq and shd_seq[-1] == '__EOL__')
        return shd_seq

    def _cnt_chars(self, dlg):
        assert dlg and dlg[-1] == '\n'
        rtxt, pcnt = re.subn(r'{[^{}]*}', '', dlg)
        rtxt = re.sub(r'\[[^{}]*\]', '', rtxt)
        rtxt = rtxt.replace('  ', '_')
        if ' ' in rtxt:
            return None, False
        return len(rtxt) - 1, pcnt

    def _chk_cnt(self, ln, dst_dlg, src_dlg, eol):
        max_cnt = 48
        cnt, pcnt = self._cnt_chars(dst_dlg)
        if cnt is None:
            self._error(ln, f'invalid space: {dst_dlg}')
        if pcnt > 0:
            scnt, spcnt = self._cnt_chars(src_dlg)
            if scnt is None:
                self._error(ln, f'invalid space: {src_dlg}')
            assert spcnt > 0
            splen = (max_cnt - scnt) // spcnt
            cnt += min(3, splen) * pcnt
        if cnt >= max_cnt:
            self._chk_cnt_tab.append((ln, dst_dlg, cnt))

    def _chk_cnt_rslt(self):
        if not self._chk_cnt_tab:
            return True
        print('overcounted dialog:')
        for ln, txt, cnt in self._chk_cnt_tab:
            print(f'{txt}@{ln}: {cnt}')
        return False

    def _chk_fnd(self, ln, dst_dlg, src_dlg, eol, dpatt):
        m = re.match(dpatt, dst_dlg)
        if not m:
            return
        val = m.group(1)
        if val is None:
            return
        rs = self._chk_fnd_tab
        rs[val] = rs.get(val, 0) + 1

    def _chk_fnd_rslt(self):
        print('found dialog:')
        for v, cnt in self._chk_fnd_tab.items():
            print(f'{v}: {cnt}')
        return True

    def _check_dialog(self, ln, dst_dlg, src_dlg, eol):
        self._chk_cnt(ln, dst_dlg, src_dlg, eol)
        #self._chk_fnd(ln, dst_dlg, src_dlg, eol, r'(\[CLR:yellow\][^\[\]{}]+\[CLR:white\])')

    def _check_result(self):
        r = True
        r = (self._chk_cnt_rslt() and r)
        #r = (self._chk_fnd_rslt() and r)
        return r

    def result(self):
        if not self._check_result():
            return None
        return super().result()

def cmp_sdialog(srcfn, dstfn, shdfn):
    cmp = c_sdialog_comparer()
    with open(srcfn, 'r', encoding = 'utf-8') as srcfd:
        with open(dstfn, 'r', encoding = 'utf-8') as dstfd:
            with open(shdfn, 'r', encoding = 'utf-8') as shdfd:
                cmp.feed(srcfd, dstfd, shdfd)
    return cmp.result()

def cmp_sdialog_lines(srclines, dstlines, shdlines):
    #cmp = c_sdialog_comparer()
    cmp = c_sdialog_comparer_check()
    cmp.feed_lines(srclines, dstlines, shdlines)
    return cmp.result()

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
