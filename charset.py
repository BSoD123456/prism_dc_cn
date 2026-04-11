#! python3
# coding: utf-8

class c_charset_jp:

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

    def enc(self, char):
        pass

    def dec(self, code):
        return self.charset.get(code, f'[{code:x}]')

if __name__ == '__main__':
    import pdb
    from hexdump import hexdump as hd
    from pprint import pprint
    ppr = lambda *a, **ka: pprint(*a, **ka, sort_dicts = False)

    def tst1():
        global cs
        cs = c_charset_jp()
    tst1()
