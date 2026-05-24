#! python3
# coding: utf-8

from sect import *

class c_fonfile(c_sect_tab):

    def _set_info(self, info):
        self.char_shape = info['shape']
        size = info.get('size', None)
        if not size is None:
            self.tsize = size
        self.rvs_byte = info.get('rvsbyt', False)
        char_bits = 1
        for v in self.char_shape:
            char_bits *= v
        self._TAB_WIDTH = char_bits // 8

    def _get_bits(self, ofs, bidx, blen, rvs, cch):
        bb = 8
        bpos = bidx // bb
        bst = bidx % bb
        bed = bst + blen
        assert(bed <= bb)
        if bpos in cch:
            byt = cch[bpos]
        else:
            byt = self.U8(ofs + bpos)
            cch[bpos] = byt
        if rvs:
            bshft = bb - bed
        else:
            bshft = bst
        return (byt >> bshft) & ((1 << blen) - 1)

    @tabitm()
    def gen_char(self, ofs):
        bs, cl, rl, bl = self.char_shape
        rvs = self.rvs_byte
        cch = {}
        for r in range(rl):
            def _rowgen():
                for b in range(bl):
                    for c in range(cl):
                        pos = ((b * rl + r) * cl + c) * bs
                        val = self._get_bits(ofs, pos, bs, rvs, cch)
                        yield val
            yield _rowgen()

    def _repack_char(self, fdat):
        def _gen(d):
            if not isinstance(d, list):
                yield d
                return
            for s in d:
                yield from _gen(s)
        bs, cl, rl, bl = self.char_shape
        rvs = self.rvs_byte
        wd = 8 // bs
        r = []
        bch = []
        for v in _gen(fdat):
            bch.append(v)
            if len(bch) < wd:
                continue
            rv = 0
            for i in range(wd):
                if rvs:
                    rv <<= bs
                    rv += bch[i]
                else:
                    rv += (bch[i] << (i * bs))
            r.append(rv)
            bch = []
        return bytearray(r)

    def _repack_with(self, finfo, **ka):
        fdats, rperm = finfo
        rmin = max(v for v in rperm if not v is None) + 1
        if not fdats:
            return self, False
        w = self._TAB_WIDTH
        rmk = self.repack_copy()
        swk = set()
        dwk = set(range(rmin))
        for dci, sci in enumerate(rperm):
            if sci is None:
                continue
            if sci in swk:
                raise ValueError(
                    f'retouched cidx in remain perm: {ci:x}')
            swk.add(sci)
            dwk.remove(dci)
            bd = self.BYTES(sci * w, w)
            rmk.WBYTES(bd, dci * w)
        for dci, fdat in zip(sorted(dwk), fdats):
            dwk.remove(dci)
            bd = self._repack_char(fdat)
            rmk.WBYTES(bd, dci * w)
        if dwk:
            raise ValueError(f'required {len(dwk)} more chars')
        fci = -1
        for fci, fdat in enumerate(fdats):
            bd = self._repack_char(fdat)
            rmk.WBYTES(bd, (rmin + fci) * w)
        rsize = rmin + fci + 1
        if rsize > self.tsize:
            report('war',
                f'new font is bigger than old: 0x{rsize:x} <- 0x{self.tsize:x}')
        return rmk, True

def font_src(fn):
    with open(fn, 'rb') as fd:
        raw = fd.read()
    fon = c_fonfile(raw, 0)
    fon.set_info({'shape': (4, 24, 24, 1)})
    fon.parse_size(len(raw), 4)
    return fon

def font_hzk(fn):
    with open(fn, 'rb') as fd:
        raw = fd.read()
    fon = c_fonfile(raw, 0)
    fon.set_info({'shape': (1, 24, 24, 1), 'rvsbyt': True})
    fon.parse_size(len(raw), 4)
    return fon
