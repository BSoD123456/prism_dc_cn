#! python3
# coding: utf-8

from report import report

import os, os.path
import subprocess

def _execmd(cmd):
    sp = subprocess.Popen(cmd,
        stderr=subprocess.STDOUT,
        stdout=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW,)
    while True:
        out = sp.stdout.readline()
        print(out.decode('mbcs'), end='')
        if sp.poll() is not None:
            break
    return sp.returncode

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

    def _info(self, msg):
        report('info', f'({self.name}) {msg}')

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
            if rname.startswith('!'):
                req = rname[1:]
            else:
                req = self.make(rname)
            reqs.append(req)
        return mkrl.make(reqs)

# === make rules ===

class c_maker_rule_alias(c_maker_rule):

    def mk0(self, req):
        return req

class c_maker_rule_path(c_maker_rule):

    def mk0(self, path):
        dpath = self.name
        if not path is None:
            dpath = os.path.join(path, dpath)
        self.path = dpath
        return dpath

class c_maker_rule_dir(c_maker_rule_path):

    def mk0(self, path):
        fn = super().mk0(path)
        if os.path.isdir(fn):
            return fn
        elif os.path.exists(fn):
            return None
        os.makedirs(fn)
        return fn

class c_maker_rule_rawfile(c_maker_rule_path):

    def mk0(self, path):
        fn = super().mk0(path)
        if not os.path.isfile(fn):
            return None
        self._info(f'load {fn}')
        with open(fn, 'rb') as fd:
            return fd.read()

class c_maker_rule_shcmd(c_maker_rule_rawfile):

    def mk1(self, path, cmdline):
        print(f'sh> {cmdline}')
        _execmd(cmdline)
        return self.mk0(path)

class c_maker_rule_extract(c_maker_rule_shcmd):

    def mk1(self, dpath, rom, wpath, cmdpatt):
        rnsp = os.path.splitext(rom)
        extname = None
        if len(rnsp) > 1:
            extname = rnsp[-1][1:].lower()
        if not extname in ('cue', 'gdi'):
            self._error(f'rom should be cue or gdi: {rom}')
        cmdline = cmdpatt.format(extname, rom, dpath, wpath)
        return super().mk1(dpath, cmdline)

class c_maker_rule_ast(c_maker_rule_rawfile):

    def mk0(self, path):
        raw = super().mk0(path)
        if raw is None:
            return None
        import pickle
        return pickle.loads(raw)

    def mk1(self, path, raw):
        self._info(f'parse ast to {self.path}')
        import pickle
        from script import c_script_file, c_script_program, SC_PROG_ENTRY
        sc = c_script_file(raw, 0)
        sc.parse_size(len(raw), 4)
        prog = c_script_program(sc)
        ast = prog.parse_sect(SC_PROG_ENTRY)
        with open(self.path, 'wb') as fd:
            pickle.dump(ast, fd)
        return ast

def make_all(paths, rom):
    rules = {}
    rules.update({
        path: (c_maker_rule_dir,)
        for path in paths.values()
    })
    rules.update({
        rom: (c_maker_rule_path, paths['source']),
    })
    rules.update({
        'SCRIPT.BIN': (
            c_maker_rule_extract, paths['extract'],
            rom, paths['work'],
            '!tools/buildgdi.exe -extract -{0} "{1}" -output "{2}" -ip "{3}/IP.BIN"',
        ),
        'FONT.DAT': (c_maker_rule_rawfile, paths['extract'], 'SCRIPT.BIN'),
        'ast.pck': (c_maker_rule_ast, paths['work'], 'SCRIPT.BIN'),
    })
    rules.update({
        'all': (c_maker_rule_alias, 'ast.pck'),
    })
    mkr = c_maker(rules)
    mkr.make('all')

if __name__ == '__main__':
    import pdb
    #from hexdump import hexdump as hd
    from pprint import pprint
    ppr = lambda *a, **ka: pprint(*a, **ka, sort_dicts = False)

    ROM = 'Prismaticallization (Japan).cue'
    PATHS = {
        'source': r'L:\Resource\Games\emu\dc\roms\Prismaticallization (Japan)',
        'output': r'',
        'work': r'wktab\work',
        'extract': r'wktab\extract',
    }

    def main():
        make_all(PATHS, ROM)
    main()
