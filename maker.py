#! python3
# coding: utf-8

from report import report

import os, os.path
import subprocess
import shutil

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

    def _get_mth(self, mn):
        mth = getattr(self, mn, None)
        if not callable(mth):
            return None, -1
        if (mth.__code__.co_flags & 0xc) != 0:
            self._error(f'invalid mk method: {mn}')
        rnum = mth.__code__.co_argcount - 1 # with self
        if rnum < 0:
            self._error(f'unbouded mk method: {mn}')
        return mth, rnum

    def make(self, lzreqs):
        rlen = len(lzreqs)
        rmax = 0
        vi = 0
        while True:
            mn = f'mk{vi}'
            vi += 1
            mth, rnum = self._get_mth(mn)
            if mth is None:
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

    def cln(self):
        pass

    def clean(self, lzreqs):
        mth, rnum = self._get_mth('cln')
        rlen = len(lzreqs)
        dreqs = []
        for i in range(rnum):
            if i < rlen:
                d, _ = lzreqs[i]()
            else:
                d = None
            dreqs.append(d)
        mth(*dreqs)
        return rnum

class c_maker:

    def __init__(self, rules):
        rl = {}
        rl_ref = {}
        for dname, (cls, *rnames) in rules.items():
            rl[dname] = (cls(dname.split('@')[0]), *rnames)
            for rname in rnames:
                if rname.startswith('!'):
                    rname = rname[1:]
                if rname in rl_ref:
                    rseq = rl_ref[rname]
                else:
                    rseq = rl_ref[rname] = []
                if not dname in rseq:
                    rseq.append(dname)
        self.rules = rl
        self.rules_ref = rl_ref
        self.cch = {}

    def _error(self, tar, msg):
        report('err', f'({tar}) {msg}')
        raise err_maker_make(msg)

    def _warn(self, tar, msg):
        report('war', f'({tar}) {msg}')

    def _chkrl(self, tarname):
        if not tarname in self.rules:
            self._error(tarname, f'unknown target')

    def _make(self, tarname):
        self._chkrl(tarname)
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

    def _clean_item(self, tarname, wk, defer):
        if tarname in wk:
            return
        wk.add(tarname)
        mkrl, *rnames = self.rules[tarname]
        lzreqs = []
        reqnames = []
        for rname in rnames:
            if rname.startswith('!'):
                rname = rname[1:]
            def mklz(rname):
                if rname.startswith('&'):
                    val = rname[1:]
                    return lambda: (val, False), None
                else:
                    return lambda: self._make(rname), rname
            lzreq, reqname = mklz(rname)
            lzreqs.append(lzreq)
            reqnames.append(reqname)
        rnum = self.rules[tarname][0].clean(lzreqs)
        defer.extend(n for n in reqnames[:rnum] if not n is None)

    def _clean_ref(self, tarname, wk, defer):
        if not tarname in self.rules_ref:
            return
        for rtar in self.rules_ref[tarname]:
            self._clean(rtar, wk, defer)

    def _clean(self, tarname, wk, defer):
        self._chkrl(tarname)
        self._clean_ref(tarname, wk, defer)
        self._clean_item(tarname, wk, defer)

    def _clean_defer(self, wk, defer):
        if defer:
            ndefer = []
            for tarname in defer:
                self._clean_item(tarname, wk, ndefer)
            if len(defer) == len(ndefer) and set(defer) == set(ndefer):
                self._error(f'looped clean')
            self._clean_defer(wk, ndefer)
        else:
            for tarname in wk:
                if tarname in self.cch:
                    self.cch.pop(tarname)

    def clean(self, tarname):
        wk = set()
        defer = []
        self._clean(tarname, wk, defer)
        self._clean_defer(wk, defer)

    def dirty(self, tarname):
        if not tarname in self.rules_ref:
            self._chkrl(tarname)
        wk = set()
        defer = []
        self._clean_ref(tarname, wk, defer)
        self._clean_defer(wk, defer)

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

    READONLY = False

    def mk0(self, path):
        fn = self.getpath(path)
        if not os.path.isfile(fn):
            return None
        self._info(f'load {fn}')
        with open(fn, 'rb') as fd:
            return fd.read()

    def cln(self, path):
        if self.READONLY:
            self._warn(f'readonly')
            return
        fn = self.getpath(path)
        if not os.path.isfile(fn):
            return
        self._info(f'remove {fn}')
        os.remove(fn)

class c_maker_rule_rawfile_readonly(c_maker_rule_rawfile):
    
    READONLY = True

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

class c_maker_rule_txtfile_readonly(c_maker_rule_txtfile):
    
    READONLY = True

class c_maker_rule_shcmd(c_maker_rule):

    def mk0(self, cmdline):
        print(f'sh> {cmdline}')
        _execmd(cmdline)
        return True

class c_maker_rule_extract(c_maker_rule_shcmd):

    def mk0(self, gdi, dpath, xpath):
        cmdpatt = 'tools/buildgdi.exe -extract -gdi "{}" -output "{}" -ip "{}/IP.BIN"'
        self._info(f'extract rom')
        gdifn = gdi[0][0]
        cmdline = cmdpatt.format(gdifn, dpath, xpath)
        return super().mk0(cmdline)

class c_maker_rule_package(c_maker_rule_shcmd):

    def mk0(self, sgdi, dpath, xpath, dgdi, opath):
        cmdpatt = 'tools/buildgdi.exe -gdi "{}" -data "{}" -ip "{}/IP.BIN" -output "{}"'
        self._info(f'package rom')
        gdifn = dgdi[0][0]
        cdda = []
        for fn, _, crit in sgdi:
            if crit:
                cdda.append(f'"{fn}"')
        cmdline = cmdpatt.format(gdifn, dpath, xpath, opath)
        if cdda:
            cmdline = ' '.join([cmdline, '-cdda', *cdda])
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

class c_maker_rule_rom_gdi(c_maker_rule_txtfile):

    def mk0(self, path):
        _, extname = os.path.splitext(self.name)
        if extname:
            extname = extname[1:].lower()
        if not extname == 'gdi':
            self._warn(f'only support gdi rom')
            return None
        lines = super().mk0(path)
        if lines is None:
            return None
        tracks = [(self.getpath(path), True, False)]
        for ln, line in enumerate(lines):
            if ln == 0 or line == '\n':
                continue
            ts = line.split()
            try:
                tt = int(ts[2].strip())
                tn = ts[4].strip()
            except:
                return None
            track = os.path.join(path, tn)
            if not os.path.isfile(track):
                self._warn(f'track not found {track}')
                return None
            ti = len(tracks)
            tracks.append((
                track,
                ti < 3 or tt != 4,
                ti > 3 and tt != 4 ))
        return tracks

class c_maker_rule_rom_gdi_copy(c_maker_rule_rom_gdi):

    def mk1(self, path, sgdi):
        fn = self.getpath(path)
        gdi = []
        for i, (track, crit, _) in enumerate(sgdi):
            if i == 0:
                dst = fn
            else:
                bn = os.path.split(track)[-1]
                dst = os.path.join(path, bn)
            gdi.append((dst, crit))
            if crit:
                if os.path.exists(dst):
                    if os.path.isfile(dst):
                        continue
                    self._warn(f'invalid track {dst}')
                    return None
                self._info(f'copy from {track}')
                shutil.copy2(track, dst)
        return gdi

def make_maker(paths, src_rom, dst_rom):
    rules = {}
    rules.update({
        path: (c_maker_rule_dir,)
        for path in paths.values()
    })
    rules.update({
        src_rom: (c_maker_rule_rom_gdi, paths['source']),
        dst_rom: (c_maker_rule_rom_gdi_copy, paths['output'], src_rom),
    })
    rules.update({
        'extract': (
            c_maker_rule_extract,
            src_rom, paths['data'], paths['extract'],
        ),
        'SCRIPT.BIN@src': (c_maker_rule_rawfile, paths['data'], 'extract'),
        'script_src.bin': (c_maker_rule_copyfile, paths['srcbak'], 'SCRIPT.BIN@src'),
        'FONT.DAT@src': (c_maker_rule_rawfile, paths['data'], 'extract'),
        'font_src.dat': (c_maker_rule_copyfile, paths['srcbak'], 'FONT.DAT@src'),
        'ast.pck': (c_maker_rule_ast, paths['work'], 'script_src.bin'),
        'code.txt': (c_maker_rule_scode, paths['work'], 'ast.pck'),
        'dialog.txt': (c_maker_rule_sdialog, paths['work'], 'ast.pck'),
        'dialog.shadow.txt': (c_maker_rule_sdialog, paths['work'], 'ast.pck'),
        'dialog_zh.txt': (c_maker_rule_txtfile_readonly, '&trans'),
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
            'font_src.dat', '&assets/ResourceHanRoundedCN-Regular.ttf',
            'mod_ast',
        ),
        'FONT.DAT@mod': (c_maker_rule_copyfile_force, paths['data'], 'font_mod.dat'),
        'modify': (c_maker_rule_vir, '!SCRIPT.BIN@mod', '!FONT.DAT@mod'),
        'package': (
            c_maker_rule_package,
            src_rom, paths['data'], paths['extract'], dst_rom, paths['output'],
            '!modify',
        ),
    })
    rules.update({
        'all': (c_maker_rule_vir, '!package'),
    })
    return c_maker(rules)

if __name__ == '__main__':
    import pdb
    #from hexdump import hexdump as hd
    from pprint import pprint
    ppr = lambda *a, **ka: pprint(*a, **ka, sort_dicts = False)

    ROM_JP = 'Prismaticallization (Japan).gdi'
    ROM_ZH = 'Prismaticallization (ZH).gdi'
    PATHS = {
        'source': r'L:\Resource\Games\emu\dc\roms\Prismaticallization (Japan)\GDI',
        'output': r'L:\Resource\Games\emu\dc\roms\Prismaticallization (Japan)\OUTPUT',
        'work': r'wktab\work',
        'extract': r'wktab\extract',
        'data': r'wktab\extract\data',
        'srcbak': r'wktab\srcbak',
    }

    def main():
        mkr = make_maker(PATHS, ROM_JP, ROM_ZH)
        mkr.make('all')
        return mkr
    mkr = main()
