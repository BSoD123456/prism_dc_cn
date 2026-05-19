#! python3
# coding: utf-8

import re

class c_charset:

    CTRLS = [
        ('LF', 0),
        None,
        ('CLR', [{0: 'white', 3: 'pink', 4: 'grey', 5: 'yellow'}]),
        ('BLINK', 1),
        ('SEL', 1),
    ]
    CTRLS_RVS = {
        CI[0]: (i, CI[1] if isinstance(CI[1], int) else [
            {v: k for k, v in tab.items()} if tab else tab
            for tab in CI[1] ] )
        for i, CI in enumerate(CTRLS) if CI }

    def dec_char(self, code):
        return None

    def enc_char(self, char):
        return None

    def decode(self, seq):
        txts = []
        slen = len(seq)
        si = 0
        while si < slen:
            code = seq[si]
            if code & 0x2000:
                cc = (code & 0x1fff)
                if cc >= len(self.CTRLS) or self.CTRLS[cc] is None:
                    raise ValueError(f'unknown ctrl code: {cc:x}')
                cmd, cfeed = self.CTRLS[cc]
                crs = [cmd]
                if isinstance(cfeed, list):
                    cflen = len(cfeed)
                    cflst = cfeed
                else:
                    cflen = cfeed
                    cflst = None
                if cflen > 0:
                    subs = []
                    for ci in range(cflen):
                        si += 1
                        if si >= slen:
                            subs.append('+')
                            continue
                        scc = (seq[si] & 0x1fff)
                        if cflst and not cflst[ci] is None:
                            if not scc in cflst[ci]:
                                raise ValueError(
                                    f'unknown sub ctrl code: {cmd}/{ci}:{scc:x}')
                            sr = cflst[ci][scc]
                        else:
                            sr = f'{scc:x}'
                        subs.append(sr)
                    subr = ','.join(subs)
                    crs.append(subr)
                cr = ':'.join(crs)
                c = f'[{cr}]'
            else:
                c = self.dec_char(code)
                if c is None:
                    raise ValueError(f'unknown char code: {code:x}')
            si += 1
            txts.append(c)
        return ''.join(txts)

    def encode(self, txt):
        seq = []
        for i, tok in enumerate(re.split(r'\[([^\[\]]+)\]', txt)):
            if i % 2 == 0:
                cch = []
                for c in tok:
                    cch.append(c)
                    code = self.enc_char(''.join(cch))
                    if not code is None:
                        seq.append(code)
                        cch.clear()
                if cch:
                    raise ValueError(f'unknown char: {"".join(cch)}')
            else:
                m = re.match(r'(\w+)(?:\s*\:\s*((?:(?:\w+|\+)(?:\s*\,\s*)?)+)|)', tok)
                if m is None:
                    raise ValueError(f'invalid ctrl: {tok}')
                cmd = m.group(1)
                if not cmd in self.CTRLS_RVS:
                    raise ValueError(f'unknown ctrl cmd: {cmd}')
                icode, iargs = self.CTRLS_RVS[cmd]
                cseq = [icode]
                cargs = m.group(2)
                if cargs is None:
                    cargs = []
                else:
                    cargs = [v.strip() for v in cargs.split(',')]
                if isinstance(iargs, int):
                    if not len(cargs) == iargs:
                        raise ValueError(f'unmatched ctrl args: {tok}')
                    cseq.extend(cargs)
                else:
                    if not len(cargs) == len(iargs):
                        raise ValueError(f'unmatched ctrl args: {tok}')
                    vargs = []
                    for si in range(len(cargs)):
                        ca = cargs[si]
                        ia = iargs[si]
                        if ia:
                            if not ca in ia:
                                raise ValueError(f'unknown ctrl arg: {ca}')
                            cseq.append(ia[ca])
                        else:
                            cseq.append(ca)
                for si, code in enumerate(cseq):
                    if isinstance(code, str):
                        if code == '+':
                            assert si == len(cseq) - 1
                            continue
                        code = int(code, 16)
                    seq.append(code | 0x2000)
        return seq

class c_charset_jp(c_charset):

    CENC = 'shift-jis'
    CHRS = [
        None,
        '  ', '、', '。', '，', '・', '：', '？', '！',
        '゛', '＿', '々', 'ー',
        '／', '～', '…', '（', '）',
        '「', '」', '『', '』', '【', '】',
        '－', '×', '＜', '＞',
        '％', '＆', '＊', '＠',
        '☆', '★', '○', '●', '□', '△', '※', '♪',
        ('0', '9'),
        ('A', 'Z'),
        ('a', 'z'),
        ('ぁ', 'ろ'),
        'わ', 'を', 'ん',
        ('ァ', 'ミ'),
        ('ム', 'ロ'),
        'ワ', 'ヲ', 'ン', 'ヴ',
        ('亜', '蔭'),
        *(
            ((hi<<8)+lr[0], (hi<<8)+lr[1])
            for hi in range(0x89, 0x97+1)
            for lr in [(0x40, 0x7e), (0x80, 0xfc)]
        ),
        ('蓮', '腕'),
        
        *'乖侑俯傲儚几刹呵',
        *'咎呟呻啜唸嗚嗅嘔',
        
        *'囓埃埒奢娶孕峙愧',
        *'慚憑憫憮懣懺拗拮',
        
        *'揉攣曖朦朧杞枷栞',
        *'棘檻鬱洸洵洒涎澹',
        
        *'狡猜猥猾瑶璧痒痙',
        *'痺瘍癇皓眩眸睨矮',
        
        *'絆綺罠羞翔脩腑膠',
        *'芻茉茹莉藪藹蠢衾',
        
        *'訝詭諍譚貪贄贅贖',
        *'赳踝蹙踪躇躊躾軋',
        
        *'轢辣迪邏靱頌頷頽',
        *'顰騙遙',
    ]

    def __init__(self):
        self.charset = self._expand_charset()
        self.charset_rvs = {v: k for k, v in self.charset.items()}

    def _char2code(self, c):
        return int(c.encode(self.CENC).hex(), 16)

    def _code2char(self, cc):
        return bytes.fromhex(hex(cc)[2:]).decode(self.CENC)

    def _expand_charset(self):
        chrset = {}
        idx = 0
        for cs in self.CHRS:
            if cs is None:
                idx += 1
            elif isinstance(cs, str):
                chrset[idx] = cs
                idx += 1
            else:
                st, ed = cs
                if st is None:
                    idx += ed
                    continue
                elif isinstance(st, str):
                    st = self._char2code(st)
                    ed = self._char2code(ed)
                for cc in range(st, ed + 1):
                    chrset[idx] = self._code2char(cc)
                    idx += 1
        return chrset

    def dec_char(self, code):
        return self.charset.get(code, None)

    def enc_char(self, char):
        return self.charset_rvs.get(char, None)

class c_charset_zh(c_charset):

    def enc_char(self, char):
        return 50

if __name__ == '__main__':
    import pdb
    from hexdump import hexdump as hd
    from pprint import pprint
    ppr = lambda *a, **ka: pprint(*a, **ka, sort_dicts = False)

    def tst1():
        global cs
        cs = c_charset_jp()
    tst1()
