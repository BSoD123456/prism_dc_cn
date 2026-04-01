#! python3
# coding: utf-8

import os, os.path
from inspect import currentframe, getframeinfo

class c_report_defer:

    def __init__(self, rpt, *na, **ka):
        self._rpt = rpt
        self._args = (na, ka)

    def __enter__(self):
        self._rpt._fold()
        return self._rpt

    def __exit__(self, *na):
        na, ka = self._args
        self._rpt._unfold(*na, **ka)

class c_report:

    def __init__(self):
        self._ign = set()
        self._fld = False

    @staticmethod
    def _print(msg):
        return print(msg)

    @staticmethod
    def _print_inline(msg):
        return print(msg, end = '')

    def _posmark(self, bk):
        cfrm = currentframe()
        for i in range(bk + 1):
            cfrm = cfrm.f_back
        frameinfo = getframeinfo(cfrm)
        return f'{frameinfo.filename}:{frameinfo.lineno}'

    def turn(self, flg, on = False):
        if on:
            if flg in self._ign:
                self._ign.remove(flg)
        else:
            self._ign.add(flg)

    def report(self, lvl, msg, *, bk = 0):
        if lvl in self._ign:
            return
        pmk = self._posmark(bk + 1)
        prpr = os.path.basename(pmk)
        rmsg = f'[{lvl}]({prpr}): {msg}'
        if self._fld:
            self._cache.append((pmk, rmsg))
        else:
            self._print(rmsg)

    def _fold(self):
        if self._fld:
            self.unfold()
        self._fld = True
        self._cache = []

    def _unfold(self, nodup = True):
        if not self._fld:
            return
        lst_pmk = None
        dup_cnt = 0
        if self._cache:
            self._cache.append((None, None))
            for pmk, rmsg in self._cache:
                if not nodup:
                    if rmsg:
                        self._print(rmsg)
                    continue
                if pmk == lst_pmk:
                    dup_cnt += 1
                else:
                    if dup_cnt > 0:
                        self._print(f' ...{dup_cnt + 1}')
                    elif lst_pmk:
                        self._print('')
                    if rmsg:
                        self._print_inline(rmsg)
                    lst_pmk = pmk
                    dup_cnt = 0
        self._cache = None
        self._fld = False

    def defer(self, *na, **ka):
        return c_report_defer(self, *na, **ka)

RPT = c_report()

def report(lvl, msg):
    RPT.report(lvl, msg, bk = 1)

if __name__ == '__main__':
    with RPT.defer():
        RPT.report('info', 'abc')
        for i in range(5):
            report('info', 'cba')
        RPT.report('info', 'abc')
        for i in range(6):
            report('info', 'cba')
