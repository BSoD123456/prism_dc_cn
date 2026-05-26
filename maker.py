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

    def make(self, lzreqs):
        rlen = len(lzreqs)
        rmax = 0
        vi = 0
        while True:
            mn = f'mk{vi}'
            vi += 1
            mth = getattr(self, mn, None)
            if not callable(mth):
                upd = False
                while rmax < rlen:
                    _, upd = lzreqs[rmax]()
                    if upd:
                        break
                    rmax += 1
                if upd:
                    vi = 0
                    continue
                break
            if (mth.__code__.co_flags & 0xc) != 0:
                self._error(f'invalid mk method: {mn}')
            rnum = mth.__code__.co_argcount - 1 # with self
            dreqs = []
            for i in range(rnum):
                if i < rlen:
                    d, _ = lzreqs[i]()
                else:
                    d = None
                dreqs.append(d)
            if rnum > rmax:
                rmax = rnum
            r = mth(*dreqs)
            if not r is None:
                return r
        self._error(f'nothing made')

class c_maker:

    def __init__(self, rules):
        self.rules = {
            dname: (cls(dname.split('@')[0]), *rnames)
            for dname, (cls, *rnames) in rules.items() }
        self.cch = {}

    def _error(self, tar, msg):
        report('err', f'({tar}) {msg}')
        raise err_maker_make(msg)

    def _warn(self, tar, msg):
        report('war', f'({tar}) {msg}')

    def _make(self, tarname):
        if not tarname in self.rules:
            self._error(tarname, f'unknown target')
        if tarname in self.cch:
            return self.cch[tarname], False
        mkrl, *rnames = self.rules[tarname]
        lzreqs = []
        for rname in rnames:
            def mklz(rname):
                if rname.startswith('&'):
                    val = rname[1:]
                    return lambda: (val, False)
                elif rname.startswith('!'):
                    val = self.make(rname[1:])
                    return lambda: (val, False)
                else:
                    return lambda: self._make(rname)
            lzreqs.append(mklz(rname))
        tar = mkrl.make(lzreqs)
        self.cch[tarname] = tar
        return tar, True

    def make(self, tarname):
        return self._make(tarname)[0]

# === make rules ===

class c_maker_rule_vir(c_maker_rule):

    def mk0(self):
        return True

class c_maker_rule_alias(c_maker_rule):

    def mk0(self, req):
        return req

class c_maker_rule_path(c_maker_rule):

    def getpath(self, path):
        dpath = self.name
        if not path is None:
            dpath = os.path.join(path, dpath)
        return dpath

    def mk0(self, path):
        return self.getpath(path)

class c_maker_rule_dir(c_maker_rule_path):

    def mk0(self, path):
        fn = self.getpath(path)
        if os.path.isdir(fn):
            return fn
        elif os.path.exists(fn):
            return None
        os.makedirs(fn)
        return fn

class c_maker_rule_rawfile(c_maker_rule_path):

    def mk0(self, path):
        fn = self.getpath(path)
        if not os.path.isfile(fn):
            return None
        self._info(f'load {fn}')
        with open(fn, 'rb') as fd:
            return fd.read()

class c_maker_rule_copyfile(c_maker_rule_rawfile):

    def mk1(self, path, raw):
        fn = self.getpath(path)
        if os.path.exists(fn):
            return None
        self._info(f'copy to {fn}')
        with open(fn, 'wb') as fd:
            fd.write(raw)
        return raw

class c_maker_rule_copyfile_force(c_maker_rule_rawfile):

    def mk0(self, path, raw):
        fn = self.getpath(path)
        if os.path.isdir(fn):
            return None
        self._info(f'force copy to {fn}')
        with open(fn, 'wb') as fd:
            fd.write(raw)
        return raw

class c_maker_rule_txtfile(c_maker_rule_rawfile):

    def mk0(self, path):
        fn = self.getpath(path)
        if not os.path.isfile(fn):
            return None
        self._info(f'load {fn} as text')
        with open(fn, 'r', encoding = 'utf-8') as fd:
            rs = []
            while True:
                line = fd.readline()
                if not line:
                    break
                rs.append(line)
            return rs

class c_maker_rule_shcmd(c_maker_rule):

    def mk0(self, cmdline):
        print(f'sh> {cmdline}')
        _execmd(cmdline)
        return True

class c_maker_rule_extract(c_maker_rule_shcmd):

    def mk0(self, rom, dpath, xpath):
        cmdpatt = 'tools/buildgdi.exe -extract -{0} "{1}" -output "{2}" -ip "{3}/IP.BIN"'
        self._info(f'extract rom')
        _, extname = os.path.splitext(rom)
        if extname:
            extname = extname[1:].lower()
        if not extname in ('cue', 'gdi'):
            self._error(f'rom should be cue or gdi: {rom}')
        cmdline = cmdpatt.format(extname, rom, dpath, xpath)
        return super().mk0(cmdline)

class c_maker_rule_ast(c_maker_rule_rawfile):

    def mk0(self, path):
        raw = super().mk0(path)
        if raw is None:
            return None
        import pickle
        import script
        return pickle.loads(raw)

    def mk1(self, path, raw):
        import pickle
        from script import c_script_file, c_script_program, SC_PROG_ENTRY
        fn = self.getpath(path)
        self._info(f'parse ast to {fn}')
        sc = c_script_file(raw, 0)
        sc.parse_size(len(raw), 4)
        prog = c_script_program(sc)
        ast = prog.parse_sect(SC_PROG_ENTRY)
        with open(fn, 'wb') as fd:
            pickle.dump(ast, fd)
        return ast

class c_maker_rule_scode(c_maker_rule_txtfile):

    def mk1(self, path, ast):
        from scode import c_scode_program, c_scode_buf_fd
        fn = self.getpath(path)
        self._info(f'gen code to {fn}')
        with open(fn, 'w', encoding = 'utf-8') as fd:
            cgen = c_scode_program(ast, c_scode_buf_fd(fd))
            cgen.gen_code()
        return self.mk0(path)

class c_maker_rule_sdialog(c_maker_rule_txtfile):

    def mk1(self, path, ast):
        from scode import c_scode_program, c_scode_buf_fd
        from sdialog import bind_sdialog_buf, bind_shadow_buf
        fn = self.getpath(path)
        bsfn, extfn = os.path.splitext(fn)
        if os.path.splitext(bsfn)[1] == '.shadow':
            bind_buf = bind_shadow_buf
        else:
            bind_buf = bind_sdialog_buf
        self._info(f'gen dialog to {fn}')
        with open(fn, 'w', encoding = 'utf-8') as fd:
            cgen = c_scode_program(ast, bind_buf(c_scode_buf_fd(fd)))
            cgen.gen_code()
        return self.mk0(path)

class c_maker_rule_rplctxt(c_maker_rule):

    def mk0(self, src, dst, shd):
        from sdcmp import cmp_sdialog_lines
        self._info(f'compare texts')
        return cmp_sdialog_lines(src, dst, shd)

class c_maker_rule_modast(c_maker_rule):

    def mk0(self, ast, rtxt):
        from smod import c_smod_program
        self._info(f'modify ast')
        cgen = c_smod_program(ast)
        ast = cgen.modify(rtxt)
        return ast, cgen.chrset

class c_maker_rule_emit(c_maker_rule_rawfile):

    def mk1(self, path, modinfo):
        from script import SC_PROG_ENTRY
        from semit import c_semit_program, c_semit_asm_buf_fd
        fn = self.getpath(path)
        ast, _ = modinfo
        conf = {
            'entries': SC_PROG_ENTRY,
            'padding': False }
        self._info(f'emit ast to {fn}')
        with open(fn, 'wb') as fd:
            emt = c_semit_program(ast, c_semit_asm_buf_fd(fd), conf)
            emt.gen_code()
        return self.mk0(path)

class c_maker_rule_emit_txt(c_maker_rule_txtfile):

    def mk1(self, path, modinfo):
        from script import SC_PROG_ENTRY
        from scode import c_scode_buf_fd
        from semit import c_semit_program
        fn = self.getpath(path)
        ast, _ = modinfo
        conf = {
            'entries': SC_PROG_ENTRY,
            'padding': False }
        self._info(f'emit ast to {fn} as text')
        with open(fn, 'w', encoding = 'utf-8') as fd:
            emt = c_semit_program(ast, c_scode_buf_fd(fd), conf)
            emt.gen_code()
        return self.mk0(path)

class c_maker_rule_font(c_maker_rule_rawfile):

    def mk1(self, path, src_font, used_font, modinfo):
        from fonmkr import make_font_ttf
        fn = self.getpath(path)
        _, chrset = modinfo
        self._info(f'make font to {fn}')
        dfon = make_font_ttf(
            src_font, used_font,
            *chrset.compact_info('，'),
            1)
        draw = dfon.BYTES()
        with open(fn, 'wb') as fd:
            fd.write(draw)
        return draw

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
        'extract': (
            c_maker_rule_extract,
            rom, paths['data'], paths['extract'],
        ),
        'SCRIPT.BIN@src': (c_maker_rule_rawfile, paths['data'], 'extract'),
        'script_src.bin': (c_maker_rule_copyfile, paths['srcbak'], 'SCRIPT.BIN@src'),
        'FONT.DAT@src': (c_maker_rule_rawfile, paths['data'], 'extract'),
        'font_src.bin': (c_maker_rule_copyfile, paths['srcbak'], 'FONT.DAT@src'),
        'ast.pck': (c_maker_rule_ast, paths['work'], 'script_src.bin'),
        'code.txt': (c_maker_rule_scode, paths['work'], 'ast.pck'),
        'dialog.txt': (c_maker_rule_sdialog, paths['work'], 'ast.pck'),
        'dialog.shadow.txt': (c_maker_rule_sdialog, paths['work'], 'ast.pck'),
        'dialog_zh.txt': (c_maker_rule_txtfile, '&trans'),
        'replace_text': (
            c_maker_rule_rplctxt,
            'dialog.txt', 'dialog_zh.txt', 'dialog.shadow.txt',
        ),
        'mod_ast': (c_maker_rule_modast, 'ast.pck', 'replace_text'),
        'script_mod.bin': (c_maker_rule_emit, paths['work'], 'mod_ast'),
        'script_mod.txt': (c_maker_rule_emit_txt, paths['work'], 'mod_ast'),
        'SCRIPT.BIN@mod': (c_maker_rule_copyfile_force, paths['data'], 'script_mod.bin'),
        'font_mod.dat': (
            c_maker_rule_font, paths['work'],
            'font_src.bin', '&assets/ResourceHanRoundedCN-Regular.ttf',
            'mod_ast',
        ),
        'FONT.DAT@mod': (c_maker_rule_copyfile_force, paths['data'], 'font_mod.dat'),
    })
    rules.update({
        'all': (c_maker_rule_vir, '!SCRIPT.BIN@mod', '!FONT.DAT@mod'),
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
        'data': r'wktab\extract\data',
        'srcbak': r'wktab\srcbak',
    }

    def main():
        make_all(PATHS, ROM)
    main()
