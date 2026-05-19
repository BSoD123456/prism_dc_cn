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

class c_font_maker:

    PAD_SEP = ' '

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
            src_name, src_size,
            dst_colors, dst_packshape, dst_offset, *,
            src_enc = 'utf-8', dst_parts = None):
        self.dshape = dst_packshape
        self.wscale = dst_packshape[0] / dst_packshape[1]
        self.doffset = dst_offset
        self._calc_decos(dst_parts, dst_colors)
        self._load_font(src_name, src_size, src_enc)

    def _calc_decos(self, parts, colors):
        if parts is None:
            parts = self.DEF_PARTS
        if isinstance(colors, int):
            colors = list(range(colors, 0, -1))
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
                _modbox(p): color
                for p in part
            }
            for part, color in zip(parts, colors)
        ]
        self.drange = (
            tuple(dbox[0]),
            tuple(
                dbox[1][i] - dbox[0][i]
                for i in range(2)
            )
        )

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
        self.fsize = size

    @staticmethod
    def _get_img_bbox(img, bcolor):
        sw, sh = img.size
        sdat = img.getdata()
        bbox = [INF, INF, -INF, -INF]
        for y in range(sh):
            for x in range(sw):
                si = y * sw + x
                c = sdat[si]
                if c == bcolor:
                    continue
                if x < bbox[0]:
                    bbox[0] = x
                if x > bbox[2]:
                    bbox[2] = x
                if y < bbox[1]:
                    bbox[1] = y
                if y > bbox[3]:
                    bbox[3] = y
        return bbox

    def _get_chars_data(self, img, sepw):
        size = self.fsize
        wscale = self.wscale
        dw, dh = self.dshape[:2]
        iw, ih = img.size
        uwidth = size + sepw
        assert ih == size and iw % uwidth == 0
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

    def _draw_chars(self, chars):
        mode = '1'
        anchor = 'lt'
        font = self.font
        size = self.fsize
        dtop = (self.dshape[1] - size) // 2
        clen = len(chars)
        sep = self.PAD_SEP
        cline = ''.join((sep, sep.join(chars), sep))
        _, _, sp_r, _ = font.getbbox(
            sep, mode = mode, anchor = anchor)
        cb_l, cb_t, cb_r, cb_b = font.getbbox(
            cline, mode = mode, anchor = anchor)
        uwidth = sp_r + size
        ov_r = cb_r - sp_r - uwidth * clen
        ov_b = cb_b - size
        if cb_l or cb_t or ov_r or ov_b > 1: # ignore ov_b == 1
            report('warning',
                'font bbox overflow: '
                f'left {cb_l} top {cb_t} rigth {ov_r} bot {ov_b}')
        img = Image.new("1", (uwidth * clen, size), color=1)
        idr = ImageDraw.Draw(img)
        idr.text((-sp_r, dtop), cline, font = font, anchor = anchor)
        return self._get_chars_data(img, sp_r)

    @staticmethod
    def _deco_char(deco, src, ssz, dst, dsz, dofs):
        dlen = len(dst)
        for si, v in enumerate(src):
            if v:
                # 0 is black, 1 is white
                continue
            sx = si % ssz[0]
            assert 0 <= sx < ssz[0]
            sy = si // ssz[0]
            assert 0 <= sy < ssz[1]
            for (px, py), dv in deco.items():
                dx = sx + px + dofs[0]
                if not 0 <= dx < dsz[0]:
                    continue
                dy = sy + py + dofs[1]
                if not 0 <= dy < dsz[1]:
                    continue
                di = dy * dsz[0] + dx
                assert 0 <= di < dlen
                dst[di] = dv

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
        chars_data = self._draw_chars(chars)
        for s in chars_data:
            drng_ofs, drng_sz = self.drange
            ssz = tuple(self.dshape[:2])
            dsz = tuple(ssz[i] + drng_sz[i] for i in range(2))
            dofs = tuple(-v for v in drng_ofs)
            d = [0] * (dsz[0] * dsz[1])
            for deco in reversed(self.decos):
                self._deco_char(deco, s, ssz, d, dsz, dofs)
            yield self._pack_char(d, dsz, self.doffset, self.dshape)

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

    def _sh(dr, seq):
        img = dr.make_img(dr.draw_chars(seq))
        img.show()
        return img

    def tst1():
        global sfon, sdr, dfon, ddr
        fn = r'wktab\FONT.DAT'
        with open(fn, 'rb') as fd:
            raw = fd.read()
        sfon = c_fonfile(raw, 0)
        sfon.set_info({'shape': (8, 12, 24, 1)})
        sfon.parse_size(len(raw), 4)
        sdr = c_font_drawer(sfon)
        dfn = 'DFYuanW5-GB.ttf'
        mkr = c_font_maker(dfn, 22, [250, 100, 50], (12, 24, 1), (0, 0))
        dfon, ddirty = sfon.repack_with((mkr.iter_chars(charset[100:200]), [0]))
        ddr = c_font_drawer(dfon)
    tst1()
