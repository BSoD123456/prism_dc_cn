#! python3
# coding: utf-8

from report import report

class c_sdialog_comparer:

    def __init__(self):
        self.txttab = {}
        self.linebuf = {}

    def _error(self, ln, msg):
        report('err', f'(ln: {ln}) {msg}')
        raise ValueError(msg)

    def _warn(self, ln, msg):
        report('war', f'(ln: {ln}) {msg}')

    def _feed_line(self, ln, src_dlg, dst_dlg, shd_dlg):
        if src_dlg == shd_dlg:
            if dst_dlg != shd_dlg:
                self._error(ln, 'unmatched lines')
            return
        self.linebuf[ln] = (src_dlg, dst_dlg, shd_dlg)

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
