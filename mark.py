#! python3
# coding: utf-8

aligned   = lambda v, a: (v % a) == 0
alignup   = lambda v, a: ((v - 1) // a + 1) * a
aligndown = lambda v, a: (v // a) * a

def readval_le(raw, offset, size, signed):
    neg = False
    v = 0
    endpos = offset + size - 1
    for i in range(endpos, offset - 1, -1):
        b = raw[i]
        if signed and i == endpos and b > 0x7f:
            neg = True
            b &= 0x7f
        #else:
        #    b &= 0xff
        v <<= 8
        v += b
    return v - (1 << (size*8 - 1)) if neg else v

def writeval_le(val, dst, offset, size):
    if val < 0:
        val += (1 << (size*8))
    for i in range(offset, offset + size):
        dst[i] = (val & 0xff)
        val >>= 8

def rvs_endian(src, size, dst_signed):
    if src < 0:
        src += (1 << (size*8))
    dst = 0
    neg = False
    for i in range(size):
        b = (src & 0xff)
        if dst_signed and i == 0 and (b & 0x80):
            neg = True
            b &= 0x7f
        dst <<= 8
        dst |= b
        src >>= 8
    return dst - (1 << (size*8 - 1)) if neg else dst

def val2bytes(val, size, be = False):
    if be:
        # singed or not never changed the result bytes
        val = rvs_endian(val, size, False)
    dst = bytearray(size)
    writeval_le(val, dst, 0, size)
    return dst

def bytes2val(raw, signed, be = False):
    size = len(raw)
    val = readval_le(raw, 0, size, signed)
    if be:
        val = rvs_endian(val, size, signed)
    return val

def lazyprop(hndl):
    nm = '_lz_' + hndl.__name__
    def _getter(self):
        if not hasattr(self, nm):
            setattr(self, nm, hndl(self))
        return getattr(self, nm)
    return property(_getter)

INF = float('inf')

c_symb = object

class c_mark:

    def __init__(self, raw, offset):
        self._raw = raw
        self._mod = None
        # mark from buf
        self.offset = offset
        self.parent = None
        self._buf_offset = 0
        self._buf_real_offset = 0

    @property
    def raw(self):
        if self.parent:
            return self.parent.raw
        return self._raw if self._mod is None else self._mod

    @property
    def mod(self):
        if self.parent:
            return self.parent.mod
        if self._mod is None:
            self._mod = bytearray(self._raw)
        return self._mod

    # buf from last buf
    @property
    def buf_offset(self):
        if self.parent:
            #assert(self._buf_offset == 0)
            return self.parent.buf_offset
        else:
            return self._buf_offset

    # buf from base
    @property
    def buf_real_offset(self):
        if self.parent:
            #assert(self._buf_real_offset == 0)
            return self.parent.buf_real_offset
        else:
            return self._buf_real_offset

    # mark from base
    @property
    def real_offset(self):
        return self.buf_real_offset + self.offset

    @property
    def accessable_top(self):
        return len(self.raw) - self.offset

    def shift(self, offs):
        self._par_offset += offs

    def extendto(self, cnt):
        extlen = self.offset + cnt - len(self.raw)
        if extlen > 0:
            self.mod.extend(bytes(extlen))

    def readval(self, pos, cnt, signed):
        return readval_le(self.raw, self.offset + pos, cnt, signed)

    def writeval(self, val, pos, cnt):
        self.extendto(pos + cnt)
        writeval_le(val, self.mod, self.offset + pos, cnt)

    def fill(self, val, pos, cnt):
        for i in range(pos, pos + cnt):
            self.mod[i] = val

    def findval(self, val, pos, cnt, signed):
        st = pos
        ed = len(self.raw) - cnt + 1 - self.offset
        for i in range(st, ed, cnt):
            s = self.readval(i, cnt, signed)
            if s == val:
                return i
        else:
            return -1

    def forval(self, cb, pos, cnt, signed):
        st = pos
        ed = len(self.raw) - cnt + 1 - self.offset
        ln = (ed - st + 1) // 2
        for i in range(st, ed, cnt):
            s = self.readval(i, cnt, signed)
            if cb(i, s, ln) == False:
                return False
        return True

    I8  = lambda self, pos: self.readval(pos, 1, True)
    U8  = lambda self, pos: self.readval(pos, 1, False)
    I16 = lambda self, pos: self.readval(pos, 2, True)
    U16 = lambda self, pos: self.readval(pos, 2, False)
    I32 = lambda self, pos: self.readval(pos, 4, True)
    U32 = lambda self, pos: self.readval(pos, 4, False)
    I64 = lambda self, pos: self.readval(pos, 8, True)
    U64 = lambda self, pos: self.readval(pos, 8, False)

    W8  = lambda self, val, pos: self.writeval(val, pos, 1)
    W16 = lambda self, val, pos: self.writeval(val, pos, 2)
    W32 = lambda self, val, pos: self.writeval(val, pos, 4)
    W64 = lambda self, val, pos: self.writeval(val, pos, 8)

    FI8 = lambda self, val, pos: self.findval(val, pos, 1, True)
    FU8 = lambda self, val, pos: self.findval(val, pos, 1, False)
    FI16 = lambda self, val, pos: self.findval(val, pos, 2, True)
    FU16 = lambda self, val, pos: self.findval(val, pos, 2, False)
    FI32 = lambda self, val, pos: self.findval(val, pos, 4, True)
    FU32 = lambda self, val, pos: self.findval(val, pos, 4, False)
    FI64 = lambda self, val, pos: self.findval(val, pos, 8, True)
    FU64 = lambda self, val, pos: self.findval(val, pos, 8, False)

    FORI8 = lambda self, cb, pos: self.forval(cb, pos, 1, True)
    FORU8 = lambda self, cb, pos: self.forval(cb, pos, 1, False)
    FORI16 = lambda self, cb, pos: self.forval(cb, pos, 2, True)
    FORU16 = lambda self, cb, pos: self.forval(cb, pos, 2, False)
    FORI32 = lambda self, cb, pos: self.forval(cb, pos, 4, True)
    FORU32 = lambda self, cb, pos: self.forval(cb, pos, 4, False)
    FORI64 = lambda self, cb, pos: self.forval(cb, pos, 8, True)
    FORU64 = lambda self, cb, pos: self.forval(cb, pos, 8, False)

    def BYTES(self, pos, cnt):
        st = self.offset + pos
        if cnt is None:
            ed = None
        else:
            ed = st + cnt
            self.extendto(pos + cnt)
        return self.raw[st: ed]

    def WBYTES(self, dst, pos):
        st = self.offset + pos
        cnt = len(dst)
        ed = st + cnt
        self.extendto(pos + cnt)
        self.mod[st: ed] = dst
        return cnt

    def STR(self, pos, cnt, codec = 'utf8'):
        return self.BYTES(pos, cnt).split(b'\0')[0].decode(codec)

    def WSTR(self, dst, pos, codec = 'utf8'):
        b = dst.encode(codec)
        if b[-1] != 0:
            b += b'\0'
        return self.WBYTES(b, pos)

    def BYTESN(self, pos):
        st = self.offset + pos
        rl = len(self.raw)
        ed = rl
        for i in range(st, rl):
            if self.raw[i] == 0:
                ed = i
                break
        return self.raw[st:ed], ed - st

    def STRN(self, pos, codec = 'utf8'):
        b, n = self.BYTESN(pos)
        return b.decode(codec), n

    def FBYTES(self, dst, pos, stp = 1):
        cnt = len(dst)
        st = self.offset + pos
        ed = len(self.raw) - cnt + 1
        for i in range(st, ed, stp):
            for j in range(cnt):
                if self.raw[i+j] != dst[j]:
                    break
            else:
                return i - self.offset
        else:
            return -1

    def FSTR(self, dst, pos, stp = 1, codec = 'utf8'):
        return self.FBYTES(dst.encode(codec), pos, stp)

    def sub(self, pos, length = None, cls = None):
        if not cls:
            cls = c_mark
        if length is None:
            s = cls(None, self.offset + pos)
            s.parent = self
        else:
            s = cls(None, 0)
            s._mod = bytearray(self.BYTES(pos, length))
            s._buf_offset = self.offset + pos
            s._buf_real_offset = self.real_offset + pos
        return s

    def concat(self, dst, pos = None):
        db = dst.BYTES(0, None)
        if pos is None:
            self.mod.extend(db)
        else:
            self.WBYTES(db, pos)
        return self
