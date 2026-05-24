#! python3
# coding: utf-8

from report import report

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

    def _error(self, msg):
        report('err', msg)
        raise ValueError(msg)

    def _warn(self, msg):
        report('war', msg)

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
                    self._error(f'unknown ctrl code: {cc:x}')
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
                                self._error(
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
                    self._error(f'unknown char code: {code:x}')
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
                    self._error(f'unknown char: {"".join(cch)}')
            else:
                m = re.match(r'(\w+)(?:\s*\:\s*((?:(?:\w+|\+)(?:\s*\,\s*)?)+)|)', tok)
                if m is None:
                    self._error(f'invalid ctrl: {tok}')
                cmd = m.group(1)
                if not cmd in self.CTRLS_RVS:
                    self._error(f'unknown ctrl cmd: {cmd}')
                icode, iargs = self.CTRLS_RVS[cmd]
                cseq = [icode]
                cargs = m.group(2)
                if cargs is None:
                    cargs = []
                else:
                    cargs = [v.strip() for v in cargs.split(',')]
                if isinstance(iargs, int):
                    if not len(cargs) == iargs:
                        self._error(f'unmatched ctrl args: {tok}')
                    cseq.extend(cargs)
                else:
                    if not len(cargs) == len(iargs):
                        self._error(f'unmatched ctrl args: {tok}')
                    vargs = []
                    for si in range(len(cargs)):
                        ca = cargs[si]
                        ia = iargs[si]
                        if ia:
                            if not ca in ia:
                                self._error(f'unknown ctrl arg: {ca}')
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

class c_charset_extendable(c_charset):

    WARN_EXT = True
    WARN_PAD = True

    def __init__(self, charset):
        self.charset = charset
        self.charset_rvs = {v: k for k, v in charset.items()}
        self.ext_chars = []

    def _charset_top(self):
        return max(self.charset.keys()) + 1

    def dec_char(self, code):
        return self.charset.get(code, None)

    def _chk_extend(self, char):
        return False, False

    def enc_char(self, char):
        code = self.charset_rvs.get(char, None)
        if code is None:
            ext, pad = self._chk_extend(char)
            if ext:
                code = self._charset_top()
                self.append(char, code)
                if self.WARN_EXT:
                    self._warn(f'extend new char: {char}')
            elif pad:
                code = self.charset_rvs.get('？', 1)
                if self.WARN_PAD:
                    self._warn(f'padding char: {char}')
        return code

    def append(self, char, code):
        assert not code in self.charset and not char in self.charset_rvs
        self.charset[code] = char
        self.charset_rvs[char] = code
        self.ext_chars.append(char)

    def update(self, charset):
        for code, char in charset.items():
            self.append(char, code)

class c_charset_base(c_charset_extendable):

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
    ]

    def __init__(self):
        super().__init__(self._expand_charset(self.CHRS, 0))

    def _char2code(self, c):
        return int(c.encode(self.CENC).hex(), 16)

    def _code2char(self, cc):
        return bytes.fromhex(hex(cc)[2:]).decode(self.CENC)

    def _expand_charset(self, chars, offs):
        chrset = {}
        idx = offs
        for cs in chars:
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

class c_charset_jp(c_charset_base):

    CENC = 'shift-jis'
    CHRS_JP = [
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
        super().__init__()
        self.update(
            self._expand_charset(self.CHRS_JP, self._charset_top()) )

class c_charset_zh_gb2312(c_charset_base):

    CENC = 'gbk'
    CHRS_ZH = [
        *(
            ((hi << 8) + 0xa1, (hi << 8) + 0xfe)
            for hi in range(0xb0, 0xd7)
        ),
        (0xd7a1, 0xd7f9),
    ]

    def __init__(self):
        super().__init__()
        self.update(
            self._expand_charset(self.CHRS_ZH, self._charset_top()) )

    def _chk_extend(self, char):
        if len(char) != 1:
            return False, False
        try:
            bs = char.encode(self.CENC)
        except:
            return False, True
        if len(bs) != 2:
            return False, False
        hi, lo = bs
        return 0x81 <= hi and 0xa1 <= lo, True

class c_charset_zh_ext(c_charset_base):

    CENC = 'gbk'
    WARN_EXT = False

    def _chk_extend(self, char):
        if len(char) != 1:
            return False, False
        try:
            bs = char.encode(self.CENC)
        except:
            return False, True
        if len(bs) != 2:
            return False, False
        hi, lo = bs
        return 0x81 <= hi and 0xa1 <= lo, True

if __name__ == '__main__':
    import pdb
    from hexdump import hexdump as hd
    from pprint import pprint
    ppr = lambda *a, **ka: pprint(*a, **ka, sort_dicts = False)

    def tst1():
        global csj, csz
        csj = c_charset_jp()
        csz = c_charset_zh_ext()
    tst1()
