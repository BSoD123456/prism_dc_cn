#! python3
# coding: utf-8

try:
    from PIL import Image, ImageDraw, ImageFont
except:
    print('''
please install Pillow with
pip3 install pillow
or
pip install pillow
or
py -3 -m pip install pillow
or
python -m pip install pillow''')
    raise

INF = float('inf')

class c_font_drawer:

    PAL = {
        1: [(255, 255, 255), (0, 0, 0)],
        4: [(255, 255, 255), (200, 200, 200), (150, 150, 150), (0, 0, 0), (255, 0, 0)]
    }

    def __init__(self, font, *, pal = None):
        self.sect = font
        if pal is None:
            fbw = font.char_shape[0]
            if fbw in self.PAL:
                pal = self.PAL[fbw]
            else:
                pal = self._monopal(fbw)
        try:
            pal_shdw = pal.index((0, 0, 0))
        except ValueError:
            pal_shdw = 1
        self.pal = pal
        self.pal_shdw = pal_shdw

    def _monopal(self, bw):
        pnum = (1 << bw)
        pstp = 256 / pnum
        assert int(pstp * pnum) == 256
        pal = []
        for i in range(pnum):
            cv = 255 - int(pstp * i)
            pal.append((cv, cv, cv))
        return pal

    def palclr(self, sel, noshadow = False):
        pal = self.pal
        shdw = self.pal_shdw
        if sel is False:
            sel = 0
        elif sel is True:
            sel = shdw
        else:
            sel = min(sel, len(pal) - 1)
            if noshadow and sel < shdw:
                sel = 0
        return pal[sel]

    def draw_char(self, cidx, *args, noshadow = False, **kargs):
        sect = self.sect
        cw = None
        for line in sect.gen_char(cidx, *args, **kargs):
            rline = []
            for v in line:
                rline.append(self.palclr(v, noshadow))
            if cw is None:
                cw = len(rline)
            yield rline, True
        while True:
            rline = []
            for x in range(cw):
                rline.append(self.palclr(False))
            yield rline, False

    def draw_comment(self, txt, pal_sel = 2):
        #ifnt = ImageFont.load_default()
        ifnt = ImageFont.truetype('msyh.ttf', 12, encoding='utf-8')
        bbox = ifnt.getbbox(txt)
        im = Image.new('RGB', bbox[2:4], self.palclr(False))
        dr = ImageDraw.Draw(im)
        dr.text((0, 0), txt, fill = self.palclr(pal_sel), font = ifnt)
        sq = im.getdata()
        w = im.width
        h = im.height
        for y in range(h):
            p = y * w
            rline = []
            for x in range(w):
                v = sq[p + x]
                rline.append(v)
            yield rline, True
        while True:
            rline = []
            for x in range(w):
                rline.append(self.palclr(False))
            yield rline, False

    def draw_padding(self, width, height):
        clr_blank = self.palclr(False)
        for y in range(height):
            rline = []
            for x in range(width):
                rline.append(clr_blank)
            yield rline, True
        while True:
            rline = []
            for x in range(width):
                rline.append(clr_blank)
            yield rline, False

    def draw_point(self, pos, cl = True, ln = 1):
        clr_blank = self.palclr(False)
        clr_black = self.palclr(cl)
        for y in range(pos):
            yield [clr_blank], True
        for y in range(ln):
            yield [clr_black], True
        while True:
            yield [clr_blank], False

    def draw_trim(self, blk, pad_left = 0, pad_right = 0,
                  trim_empty = False, trim_val = False):
        clr_blank = self.palclr(False)
        clr_trim = self.palclr(trim_val)
        cchl = []
        lmin = INF
        rmin = INF
        for rl, uf in blk:
            if not uf:
                break
            cchl.append(rl)
            if lmin > 0:
                lblnk = 0
                for v in rl:
                    if v != clr_trim:
                        break
                    lblnk += 1
                else:
                    # all blank
                    continue
                if lblnk < lmin:
                    lmin = lblnk
            if rmin > 0:
                rblnk = 0
                for v in reversed(rl):
                    if v != clr_trim:
                        break
                    rblnk += 1
                else:
                    # all blank
                    continue
                if rblnk < rmin:
                    rmin = rblnk
        if rmin == INF:
            assert(lmin == INF)
            if trim_empty:
                lmin = rmin = 0
            else:
                lmin = 0
                rmin = None
        elif rmin == 0:
            rmin = None
        else:
            rmin = -rmin
        if pad_left > 0:
            pll = []
            for _ in range(pad_left):
                pll.append(clr_blank)
        w = 0
        for rl in cchl:
            rl = rl[lmin:rmin]
            if pad_left > 0:
                rl = pll + rl
            if pad_right > 0:
                for _ in range(pad_right):
                    rl.append(clr_blank)
            w = len(rl)
            yield rl, True
        rline = []
        for x in range(w):
            rline.append(clr_blank)
        while True:
            yield rline, False

    def draw_horiz(self, *blks, pad = 5, trim = 0):
        clr_blank = self.palclr(False)
        rwidth = 0
        while True:
            unfinished = False
            rline = []
            blen = len(blks)
            for i in range(blen):
                blk = blks[i]
                rl, uf = next(blk)
                if uf:
                    unfinished = True
                if trim > 0:
                    rl = rl[:-trim]
                rline.extend(rl)
                if i < blen -1:
                    for x in range(pad):
                        rline.append(clr_blank)
            if not rwidth:
                rwidth = len(rline)
            if unfinished:
                yield rline, True
            else:
                break
        while True:
            rline = []
            for x in range(rwidth):
                rline.append(clr_blank)
            yield rline, False

    def draw_vert(self, *blks, pad = 10):
        clr_blank = self.palclr(False)
        blk_info = []
        for blk in blks:
            rl, uf = next(blk)
            if uf:
                blk_info.append((blk, rl, len(rl)))
        rwidth = max(p[2] for p in blk_info)
        blen = len(blk_info)
        for i in range(blen):
            blk, rl, rlen = blk_info[i]
            rl_pad = []
            for x in range(rwidth - rlen):
                rl_pad.append(clr_blank)
                rl.append(clr_blank)
            yield rl, True
            for rl, uf in blk:
                if not uf:
                    break
                if rl_pad:
                    rl.extend(rl_pad)
                yield rl, True
            if i < blen - 1:
                for y in range(pad):
                    rline = []
                    for x in range(rwidth):
                        rline.append(clr_blank)
                    yield rline, True
        while True:
            rline = []
            for x in range(rwidth):
                rline.append(clr_blank)
            yield rline, False

    def make_img(self, blk):
        dat = []
        bh = 0
        bw = 0
        for rl, uf in blk:
            if not uf:
                break
            if not bw:
                bw = len(rl)
            dat.extend(rl)
            bh += 1
        im = Image.new('RGB', (bw, bh))
        im.putdata(dat)
        return im

    def draw_chars(self, chars, pad = 2, trim = -1, **kargs):
        if trim < 0:
            trim = 0
            autotrim = True
        else:
            autotrim = False
        blks = []
        for char in chars:
            blk = self.draw_char(char, **kargs)
            if autotrim:
                blk = self.draw_trim(blk)
            blks.append(blk)
        return self.draw_horiz(*blks, pad = pad, trim = trim)

if __name__ == '__main__':
    import pdb
    from hexdump import hexdump as hd
    from pprint import pprint
    ppr = lambda *a, **ka: pprint(*a, **ka, sort_dicts = False)

    from fonfile import c_fonfile

    def _show(gen):
        img = dr.make_img(gen)
        img.show()
        return img

    def tst1():
        global fon, dr
        fn = r'wktab\FONT.DAT'
        with open(fn, 'rb') as fd:
            raw = fd.read()
        fon = c_fonfile(raw, 0)
        fon.set_info({'shape': (8, 12, 24, 1)})
        fon.parse_size(len(raw), 4)
        dr = c_font_drawer(fon)
    tst1()
