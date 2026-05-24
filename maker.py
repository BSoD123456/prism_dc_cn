#! python3
# coding: utf-8

from report import report

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
        while True
            mn = f'mk{vi}'
            vi += 1
            mth = getattr(self, mn, None)
            if not callable(mth):
                break
            try:
                r = mth(*reqs)
            except TypeError as ex:
                if 'argument' in ex.args[0]:
                    self._error(f'unmatched requires: {len(reqs)}')
                else:
                    raise
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
        mkrl, *rnames = self.rules(tarname)
        reqs = []
        for rname in rnames:
            reqs.append(self.make(rname))
        return mkrl.make(reqs)

# === make rules ===

class c_maker_rule_key(c_maker_rule):

    def mk0(self, key):
        return key

class c_maker_rule_rawfile(c_maker_rule):

    def mk0(self):
        with open(self.name, 'rb') as fd:
            return fd.read()

def main():
    pass

if __name__ == '__main__':
    import pdb
    #from hexdump import hexdump as hd
    from pprint import pprint
    ppr = lambda *a, **ka: pprint(*a, **ka, sort_dicts = False)
