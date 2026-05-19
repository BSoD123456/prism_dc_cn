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
        self.ssize = src_size
        self.dshape = dst_packshape
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
        iw, ih = img.size
        uwidth = size + sepw
        assert ih == size and iw % uwidth == 0
        clen = iw // (size + sepw)
        rs = [[] for _ in range(clen)]
        for i, v in enumerate(img.getdata()):
            lx = i % iw
            ci = lx // uwidth
            cx = lx % uwidth
            if cx < size:
                rs[ci].append(v)
        assert all(len(c) == size ** 2 for c in rs)
        return rs

    def _draw_chars(self, chars):
        mode = '1'
        anchor = 'lt'
        font = self.font
        size = self.fsize
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
        idr.text((-sp_r, 0), cline, font = font, anchor = anchor)
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
            ssz = tuple(self.ssize for _ in range(2))
            dsz = tuple(ssz[i] + drng_sz[i] for i in range(2))
            dofs = tuple(-v for v in drng_ofs)
            d = [0] * (dsz[0] * dsz[1])
            for deco in reversed(self.decos):
                self._deco_char(deco, s, ssz, d, dsz, dofs)
            yield self._pack_char(d, dsz, self.doffset, self.dshape)

def make_font_maker(name, size, shape, offset, clrofs = 0):
    return c_font_maker(name, size,
        ((1 << shape[0]) - 1) - clrofs, shape[1:], offset)

if __name__ == '__main__':
    import pdb
    from hexdump import hexdump as hd
    from pprint import pprint
    ppr = lambda *a, **ka: pprint(*a, **ka, sort_dicts = False)

    #foo = make_font_maker('msyh', 12, (4,8,16,2), (1, 2), 5)
    #foo = make_font_maker('msyh', 12, (1,12,12,1), (0, 0))
    #bar = make_font_maker('03_DFYuanW5-GB.ttf', 12, (1,12,12,1), (0, 0))
    #bar = foo.get_char('好')
    bar = make_font_maker('msyh', 24, (8,12,24,1), (0, 0))
    def _draw_darr(arr, condi = None):
        if condi is None:
            condi = lambda v: v
        print('-' * 50)
        for y in range(0, 18*16, 18):
            print(f'{y:03d}:', ' '.join(
                f'{arr[y+i]:01d}' if condi(arr[y+i]) else ' '
                for i in range(18)))
    #_draw_darr(bar)
    #_draw_darr(bar, lambda v: v == 4)
    #_draw_darr(bar, lambda v: v == 3)
    #_draw_darr(bar, lambda v: v == 5)
    def _draw_tester():
        img = Image.new("1", (100, 50), color=1)
        idr = ImageDraw.Draw(img)
        def _tst(mkr, s, an='la', bot=False, shw=True):
            idr.rectangle([(0, 0), (100, 50)], fill='white')
            if bot:
                pos = (0, 15)
            else:
                pos = (0, 3)
            idr.line([(0, 3), (100, 3)])#, fill='blue')
            idr.line([(0, 15), (100, 15)])#, fill='red')
            idr.text(pos, s, anchor=an, font=mkr.font, spacing=0)#, fill='black')
            #print('bbox:', img.getbbox())
            print('bbox:', idr.textbbox((0, 0), s, anchor=an, font=mkr.font, spacing=0))
            if shw:
                img.show()
        return _tst
    _drw_tst = _draw_tester()
    #_drw_tst(bar, '\n啊\n啊', 'la')
    #_drw_tst(bar, '\n啊\n好啊', 'la')
    _drw_tst(bar, '\n好啊\n好啊', 'la')
    charset = ''
    def _get_highest_char(mkr, an='la'):
        font = mkr.font
        xh = (-INF, [])
        xb = (-INF, [])
        for c in charset:
            _, t, _, b = font.getbbox(c, mode = '1', anchor = an)
            h = b - t
            if h > xh[0]:
                xh = (h, [c])
            elif h == xh[0]:
                xh[1].append(c)
            if b > xb[0]:
                xb = (b, [c])
            elif b == xb[0]:
                xb[1].append(c)
        return xh, xb
    def _chk_char_width(mkr, step = 100, an='la'):
        ka = {
            'mode': '1',
            'anchor': an,
        }
        font = mkr.font
        sep = ' '
        l, _, r, _ = font.getbbox(sep, **ka)
        sepw = r - l
        for i in range(len(charset)):
            if i % step == 0:
                print(i)
                schrsl = charset[i:i+step]
                schrs = ''.join(c + sep for c in schrsl)
                assert len(schrs) == len(schrsl) * 2
                sst = i
                #sumwidth = 0
            #c = charset[i]
            s = schrs[:(i-sst+1)*2]
            #l, _, r, _ = font.getbbox(c, **ka)
            #cw = 12#r - l
            l, _, r, _ = font.getbbox(sep + s, **ka)
            assert l == 0
            sw = r - sepw#r - l
            #if sumwidth + cw + sepw != sw:
            #    print(f'({s[-4] if len(s) > 2 else ""}){c}: should:{cw} / real:{sw - sumwidth - sepw}')
            ssw = (12 + sepw) * len(s) / 2
            if sw != ssw:
                print(f'({s[-4] if len(s) > 2 else ""}){s[-2]}: should:{12 + sepw} / real:{sw - ssw + (12 + sepw)}')
                breakpoint()
            #sumwidth += cw + sepw
        else:
            print('done')

