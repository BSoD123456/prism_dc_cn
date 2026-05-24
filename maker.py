#! python3
# coding: utf-8

from report import report

import os, os.path

class err_maker_make(ValueError):
    pass

class c_maker_rule:

    def __init__(self, name):
        self.name = name

    def _error(self, msg):
        report('err', f'({self.name}) {msg}')
        raise err_maker_make(msg)

    def _warn(self, msg):
        report('war', f'({self.name}) {msg}')

    def make(self, reqs):
        vi = 0
        while True:
            mn = f'mk{vi}'
            vi += 1
            mth = getattr(self, mn, None)
            if not callable(mth):
                break
            if (mth.__code__.co_flags & 0xc) != 0:
                self._error(f'invalid mk method: {mn}')
            rnum = mth.__code__.co_argcount - 1 # with self
            dreqs = []
            rlen = len(reqs)
            for i in range(rnum):
                if i < rlen:
                    d = reqs[i]
                else:
                    d = None
                dreqs.append(d)
            r = mth(*dreqs)
            if not r is None:
                return r
        self._error(f'nothing made')

class c_maker:

    def __init__(self, rules):
        self.rules = {
            dname: (cls(dname), *rnames)
            for dname, (cls, *rnames) in rules.items() }

    def _error(self, tar, msg):
        report('err', f'({tar}) {msg}')
        raise err_maker_make(msg)

    def _warn(self, tar, msg):
        report('war', f'({tar}) {msg}')

    def make(self, tarname):
        if not tarname in self.rules:
            self._error(tarname, f'unknown target')
        mkrl, *rnames = self.rules[tarname]
        reqs = []
        for rname in rnames:
            reqs.append(self.make(rname))
        return mkrl.make(reqs)

# === make rules ===

class c_maker_rule_key(c_maker_rule):

    def mk0(self, key):
        return key

class c_maker_rule_vir(c_maker_rule):

    def mk0(self):
        return True

class c_maker_rule_path(c_maker_rule):

    def mk0(self, path):
        dpath = self.name
        if not path is None:
            dpath = os.path.join(path, dpath)
        self.path = dpath

class c_maker_rule_dir(c_maker_rule_path):

    def mk0(self, path):
        super().mk0(path)
        fn = self.path
        if os.path.isdir(fn):
            return fn
        elif os.path.exists(fn):
            return None
        os.makedirs(fn)
        return fn

class c_maker_rule_rawfile(c_maker_rule):

    def mk0(self, path):
        super().mk0(path)
        fn = self.path
        if not os.path.isfile(fn):
            return None
        with open(fn, 'rb') as fd:
            return fd.read()

def make_all(paths):
    rules = {}
    rules.update({
        path: (c_maker_rule_dir,)
        for path in paths.values()
    })
    rules.update({
        
    })
    rules.update({
        'all': (c_maker_rule_vir, paths['work'], paths['extract']),
    })
    mkr = c_maker(rules)
    mkr.make('all')

if __name__ == '__main__':
    import pdb
    #from hexdump import hexdump as hd
    from pprint import pprint
    ppr = lambda *a, **ka: pprint(*a, **ka, sort_dicts = False)

    PATHS = {
        'work': 'wktab2/work',
        'extract': 'wktab2/extract',
    }

    def main():
        make_all(PATHS)
    main()
