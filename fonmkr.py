#! python3
# coding: utf-8

from sect import report, INF

try:
    from PIL import Image, ImageDraw, ImageFont
except:
    print('''Install Pillow with
pip3 install pillow
or
pip install pillow
''')
    raise

class c_font_source:
    pass

class c_font_source_pil(c_font_source):

    PAD_SEP = ' '

    def __init__(
            self, name, size, colors, dshape, *,
            scale = 1, enc = 'utf-8'):
        self.size = size
        self.sscale = scale
        self.scolors = colors
        self.dshape = dshape
        self.dscale = dshape[0] / dshape[1]
        self.wscale = self.dscale / self.sscale
        self._load_font(name, size, enc)

    def _load_font(self, name, size, enc):
        def _iname():
            yield name
            yield f'wktab\\{name}'
        for dname in _iname():
            try:
                font = ImageFont.truetype(dname, size, encoding = enc)
            except OSError:
                pass
            else:
                break
        else:
            raise ValueError(f'invalid font: {name}')
        self.font = font

    def _draw_chars(self, chars):
        mode = '1'
        anchor = 'lt'
        font = self.font
        size = self.size
        dw, dh = self.dshape[:2]
        dtop = (dh - size) // 2
        clen = len(chars)
        sep = self.PAD_SEP
        cline = ''.join((sep, sep.join(chars), sep))
        _, _, sp_r, _ = font.getbbox(
            sep, mode = mode, anchor = anchor)
        cb_l, cb_t, cb_r, cb_b = font.getbbox(
            cline, mode = mode, anchor = anchor)
        uwidth = sp_r + size
        ov_r = cb_r - sp_r - uwidth * clen
        ov_b = cb_b - dh
        if cb_l or cb_t or ov_r or ov_b > 1: # ignore ov_b == 1
            report('warning',
                'font bbox overflow: '
                f'left {cb_l} top {cb_t} rigth {ov_r} bot {ov_b}')
        img = self._draw_chars_img(
            cline, (-sp_r, dtop), (uwidth * clen, dh),
            font, anchor)
        return img, sp_r

    def _get_chars_data(self, img, sepw):
        size = self.size
        wscale = self.wscale
        dw, dh = self.dshape[:2]
        iw, ih = img.size
        uwidth = size + sepw
        assert ih == dh and iw % uwidth == 0
        clen = iw // uwidth
        rs = [[1 for _ in range(dw * dh)] for _ in range(clen)]
        for i, v in enumerate(img.getdata()):
            y = i // iw
            lx = i % iw
            ci = lx // uwidth
            cx = lx % uwidth
            scx = int(cx * wscale)
            if scx < dw:
                rs[ci][scx + y * dw] &= v
        return rs

    def get_chars_data(self, chars):
        img, sepw = self._draw_chars(chars)
        return self._get_chars_data(img, sepw)

    def _draw_chars_img(self, cline, offset, size, font, anchor):
        raise NotImplementedError()

    def get_color(self, src_color, dst_part):
        raise NotImplementedError()

class c_font_source_pil1b(c_font_source_pil):

    def _draw_chars_img(self, cline, offset, size, font, anchor):
        img = Image.new("1", size, color=1)
        idr = ImageDraw.Draw(img)
        idr.text(offset, cline, font = font, anchor = anchor)
        return img

    def get_color(self, src_color, dst_part):
        if src_color == 1:
            return None
        else:
            return self.scolors[dst_part]

class c_font_maker:

    DEF_PARTS = [
        # center
        [
            ( 0,  0),
        ],
        # shadow
        [
            ( 1,  0),
            ( 1,  1),
        ],
        # outline
        [
            (-1, -1),
            ( 0, -1),
            ( 1, -1),
            (-1,  0),
            ( 1,  0),
            (-1,  1),
            ( 0,  1),
            ( 1,  1),
        ],
    ]

    def __init__(self,
            source, offset, *,
            deco_parts = None):
        self.source = source
        self.shape = source.dshape
        self.offset = offset
        self._calc_decos(deco_parts)

    def _calc_decos(self, parts):
        if parts is None:
            parts = self.DEF_PARTS
        dbox = [[INF, INF], [-INF, -INF]]
        def _modbox(pos):
            for i, v in enumerate(pos):
                vec = dbox[0]
                if v < vec[i]:
                    vec[i] = v
                vec = dbox[1]
                if v > vec[i]:
                    vec[i] = v
            return pos
        self.decos = [
            {
                _modbox(p): idx
                for p in part
            }
            for idx, part in enumerate(parts)
        ]
        self.drange = (
            tuple(dbox[0]),
            tuple(
                dbox[1][i] - dbox[0][i]
                for i in range(2)
            )
        )

    def _deco_char(self, deco, src, ssz, dst, dsz, dofs):
        dlen = len(dst)
        for si, v in enumerate(src):
            sx = si % ssz[0]
            assert 0 <= sx < ssz[0]
            sy = si // ssz[0]
            assert 0 <= sy < ssz[1]
            for (px, py), dv in deco.items():
                clr = self.source.get_color(v, dv)
                if clr is None:
                    continue
                dx = sx + px + dofs[0]
                if not 0 <= dx < dsz[0]:
                    continue
                dy = sy + py + dofs[1]
                if not 0 <= dy < dsz[1]:
                    continue
                di = dy * dsz[0] + dx
                assert 0 <= di < dlen
                dst[di] = clr

    @staticmethod
    def _peek_char_val(src, ssz, dofs, shp, pos):
        dim = 2
        dv = [1] * dim
        pr = [-i for i in dofs[:dim]]
        for zi, (pv, sv) in enumerate(zip(pos, shp)):
            pr[zi % dim] += pv * dv[zi % dim]
            dv[zi % dim] *= sv
        if not (0 <= pr[0] < ssz[0]
            and 0 <= pr[1] < ssz[1]):
            return 0
        pi = pr[1] * ssz[0] + pr[0]
        return src[pi]

    def _pack_char(self, src, ssz, dofs, shp, pos = None, si = None):
        if si is None:
            si = len(shp) - 1
        if pos is None:
            pos = [0] * len(shp)
        if si < 0:
            return self._peek_char_val(src, ssz, dofs, shp, pos)
        rng = shp[si]
        r = []
        for i in range(rng):
            npos = pos.copy()
            npos[si] = i
            r.append(self._pack_char(src, ssz, dofs, shp, npos, si - 1))
        return r

    def iter_chars(self, chars):
        chars_data = self.source.get_chars_data(chars)
        for s in chars_data:
            drng_ofs, drng_sz = self.drange
            ssz = tuple(self.shape[:2])
            dsz = tuple(ssz[i] + drng_sz[i] for i in range(2))
            dofs = tuple(-v for v in drng_ofs)
            d = [0] * (dsz[0] * dsz[1])
            for deco in reversed(self.decos):
                self._deco_char(deco, s, ssz, d, dsz, dofs)
            yield self._pack_char(d, dsz, self.offset, self.shape)

if __name__ == '__main__':
    import pdb
    from hexdump import hexdump as hd
    from pprint import pprint
    ppr = lambda *a, **ka: pprint(*a, **ka, sort_dicts = False)

    charset = [
        bytes([high, low]).decode('gb2312')
        for high in range(0xB0, 0xD8)
        for low in range(0xA1, 0xFF)
        if high != 0xD7 or low <= 0xD9
    ]
    
    from fonfile import c_fonfile
    from fondrw import c_font_drawer

    def sh(dr, seq):
        img = dr.make_img(dr.draw_chars(seq))
        img.show()
        return img

    def tst1():
        global sfon, sdr, dfon, ddr
        fn = r'wktab\FONT.DAT'
        with open(fn, 'rb') as fd:
            raw = fd.read()
        sfon = c_fonfile(raw, 0)
        #sfon.set_info({'shape': (8, 24, 24, 1)})
        sfon.set_info({'shape': (8, 12, 24, 1)})
        sfon.parse_size(len(raw), 4)
        sdr = c_font_drawer(sfon)
        dfn = 'DFYuanW5-GB.ttf'
        fsrc = c_font_source_pil1b(dfn, 22, [250, 100, 50], (12, 24, 1))
        mkr = c_font_maker(fsrc, (0, 0))
        cs = charset[100:200]
        #cs = '卑'
        dfon, ddirty = sfon.repack_with((mkr.iter_chars(cs), [0]))
        ddr = c_font_drawer(dfon)
    tst1()
