#! python3
# coding: utf-8

from mark import c_mark

class c_script(c_mark):

    def findstr(self, st = 0, ed = None, **kargs):
        rb = []
        idx = [0]
        rs = []
        def fnd(i, val, ln):
            if ed and i > ed:
                return False
            if val >> 0x1b != 0x11:
                return
            b1 = (val & 0x1fff)
            if b1 == 0x1fff:
                if rb:
                    rs.append(rb)
                    #print(f'{idx[0]:x}:', ' '.join(f'{b: 4x}' for b in rb))
                    print(f'{idx[0]:x}:', self.test_dec(rb, **kargs))
                rb.clear()
                return
            if not rb:
                idx[0] = i
            rb.append(b1)
            b2 = ((val >> 0xd) & 0x1fff)
            if b2 != 0x1fff:
                rb.append(b2)
        self.forval(fnd, st, 4, False)

    def test_dec(self, bs, kofs = 0):
        chrj = lambda c: int(c.encode('shift-jis').hex(), 16)
        tst_cs = [
            (0x66, chrj('ゐ') - chrj('ぁ') + 1, chrj('ぁ')),
            (0, chrj('ヂ') - chrj('ァ') + 1, chrj('ァ')),
            (0, chrj('ミ') - chrj('ツ') + 1, chrj('ツ')),
            (0, chrj('ヶ') - chrj('ム') + 1, chrj('ム')),
        ]
        tst_rplc = {
            'ヱ': 'ー',
            'ゎ': 'わ',
            'わ': 'を',
            'ゐ': 'ん',
            '[c]': 'ッ',
        }
        rs = []
        need_check = False
        for b in bs:
            cbs = 0
            for cs in tst_cs:
                cbs += cs[0]
                if cbs <= b < cbs + cs[1]:
                    r = bytes.fromhex(hex(b - cbs + cs[2])[2:]).decode('shift-jis')
                    break
                cbs += cs[1]
            else:
                if 0x60 < b < 0x70: #or 0x100 < b < 0x120:
                    print(hex(b))
                    breakpoint()
                r = f'[{b:x}]'
            if r in tst_rplc:
                r = tst_rplc[r]
            if r in '?ゑ':
                need_check = True
            rs.append(r)
        if need_check:
            print('check:', ''.join(rs))
            breakpoint()
        return ''.join(rs)

def main(fn):
    with open(fn, 'rb') as fd:
        raw = fd.read()
    sc = c_script(raw, 0)
    if True:
        sc.findstr()
    else:
        for i in range(-0x10, 0x10):
            print(i, '===')
            #sc.findstr(0xe810, 0xe938, kofs = i)
            sc.findstr(0x4878c, 0x487c4, kofs = i)
    return sc

if __name__ == '__main__':
    import pdb
    #from hexdump import hexdump as hd
    from pprint import pprint
    ppr = lambda *a, **ka: pprint(*a, **ka, sort_dicts = False)

    main(r'wktab\SCRIPT.BIN')
