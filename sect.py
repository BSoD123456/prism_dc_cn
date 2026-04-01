#! python3
# coding: utf-8

from mark import *
from report import report

class c_sect(c_mark):

    ADDR_BASE = 0x8000000

    _SECT_ALIGN = 1
    _SECT_TOP_ALIGN = 1

    def BYTES(self, pos = 0, cnt = -1):
        if cnt and cnt < 0 or pos < 0:
            if self.is_parsed:
                tp = self.sect_top
            else:
                tp = self.accessable_top
            if pos < 0:
                pos = tp + pos
            if cnt and cnt < 0:
                cnt = tp - pos
        return super().BYTES(pos, cnt)

    def set_info(self, *na):
        self._sect_setinfo = na
        return self._set_info(*na)

    def _set_info(self, *na):
        pass

    def parse(self):
        pass

    def parse_size(self, top_ofs, top_align_width):
        assert(self.real_offset % self.sect_align == 0)
        self._sect_top = top_ofs
        self._sect_real_top = None
        self._sect_top_nondeterm = False
        if isinstance(top_align_width, tuple):
            self._sect_top_align = top_align_width[0]
            self._sect_top_align_max = top_align_width[1]
        else:
            self._sect_top_align = top_align_width
            self._sect_top_align_max = top_align_width

    @property
    def is_parsed(self):
        return hasattr(self, '_sect_top')

    @property
    def sect_align(self):
        return self._SECT_ALIGN

    @property
    def sect_top_align(self):
        return max(self._sect_top_align, self._SECT_TOP_ALIGN)

    @property
    def sect_top(self):
        return self._sect_top

    @property
    def sect_top_least(self):
        sect_top = self.sect_top
        if sect_top is None:
            return 0
        else:
            return sect_top

    @property
    def sect_top_nondeterm(self):
        return self._sect_top_nondeterm

    def set_nondeterm(self):
        self._sect_top_nondeterm = True

    def set_real_top(self, real_top):
        align = self.sect_top_align
        align_max = self._sect_top_align_max
        real_offset = self.real_offset
        if self._sect_top is None:
            real_offset_top = alignup(real_offset + real_top, align)
            self._sect_top = real_offset_top - real_offset
            self._sect_real_top = real_top
            return
        if 0 <= self._sect_top - real_top < align_max:
            self._sect_real_top = real_top
            return
        if self._sect_top_nondeterm:
            real_offset_top = alignup(real_offset + real_top, align)
            self._sect_top = real_offset_top - real_offset
            self._sect_real_top = real_top
            return
        else:
            raise ValueError('sect error: invalid real top')

    def in_sect(self, offs):
        return 0 <= offs and (self._sect_top is None or offs < self._sect_top)

    def aligned_sect_top(self, base = 0):
        return alignup(self.sect_top + base, self.sect_top_align) - base

    def sub(self, pos, length = None, cls = None):
        if length is None and not self.in_sect(pos):
            raise ValueError('sect error: sub sect overflow')
        return super().sub(pos, length, cls)

    def sub_simplest(self, pos, top, top_align = 1):
        sub = self.sub(pos, cls = c_sect)
        sub.parse_size(top, top_align)
        return sub

    def _offs2addr(self, offs):
        return offs + self.real_offset + self.ADDR_BASE

    def _addr2offs(self, addr):
        return addr - self.ADDR_BASE - self.real_offset

    def aot(self, v, typ):
        if typ[0] == typ[1]:
            return v
        elif typ[0] == 'a':
            assert(typ == 'ao')
            return self._addr2offs(v)
        else:
            assert(typ == 'oa')
            return self._offs2addr(v)

    def rdptr(self, ptr, typ = 'oao'):
        if typ[0] == 'a':
            ptr = self._addr2offs(ptr)
        return self.aot(self.U32(ptr), typ[1:])

    def repack_copy(self, sect_top = None):
        if sect_top is None:
            sect_top = self.sect_top
        if sect_top is None:
            raise ValueError('can not copy non-top sect')
        return self.sub(0, sect_top, cls = type(self))

    def repack_with_copy(self, **kargs):
        rmk = self.repack_copy()
        self._repack_end(rmk, **kargs)
        return rmk

    def realign(self, align, base, pad = None, ext = 0, min_top = 0):
        ac_top = self.accessable_top + ext
        ac_top = max(min_top, ac_top)
        ac_top += base
        align_top = alignup(ac_top, align)
        add_top = align_top - base - self.accessable_top
        if add_top > 0:
            if pad is None:
                pb = bytes(add_top)
            else:
                pb = bytes([pad]) * add_top
            self.WBYTES(pb, self.accessable_top)
        return align_top

    def _repack_pad(self):
        return None

    def _repack_sub_with(self, schr, sub, tab, sofs, **kargs):
        return sub.repack_with(tab, **kargs)

    def _resizable_sub(self, schr, ssub):
        return True

    def compact_holder(self, hkey, hlen, halign = 1):
        return (hkey, hlen, halign)

    def is_compact_holder(self, hld):
        return isinstance(hld, tuple)

    def repack_compact(self, itr_pck, base = 0, pad = None, **kargs):
        dirty = False
        hole = False
        srmks = []
        cent = base
        ent_cch = {}
        ents = []
        for schr, ssub, dval in itr_pck:
            if ssub is None:
                ents.append((0, 0))
                srmks.append(None)
                continue
            elif self.is_compact_holder(ssub):
                hkey, hlen, halign = ssub
                ents.append((cent, hlen))
                cent = alignup(cent + hlen, halign)
                srmks.append(hkey)
                hole = True
                continue
            if not schr is None and schr in ent_cch:
                ents.append(ent_cch[schr])
                srmks.append(None)
                continue
            if not dval is None:
                srmk, sdirty = self._repack_sub_with(schr, ssub, dval, cent, pad = pad, **kargs)
                if sdirty:
                    dirty = True
            else:
                srmk = ssub
                sdirty = False
            rent = (cent, srmk.sect_top)
            if not sdirty:
                srmk = srmk.repack_with_copy(pad = pad, **kargs)
            if not schr is None:
                ent_cch[schr] = rent
            ents.append(rent)
            if self._resizable_sub(schr, ssub):
                cent = srmk.realign(ssub.sect_top_align, cent, pad)
            else:
                satop = ssub.aligned_sect_top(cent)
                if srmk.sect_top > satop:
                    raise ValueError(
                        f'unresizable sub overflow: {srmk.sect_top:x}/{satop:x}')
                cent = srmk.realign(
                    ssub.sect_top_align, cent, pad,
                    min_top = satop)
            srmks.append(srmk)
        if dirty or hole:
            return srmks, ents, cent - base, dirty
        else:
            return None, None, None, False

    def _repack_setinfo(self, rmk, setinfo, **ka):
        return setinfo, False

    @property
    def sect_dirty_setinfo(self):
        if not (hasattr(self, '_sect_setinfo_dirty')
                and self._sect_setinfo_dirty):
            return None
        return self._sect_setinfo

    def _repack_end(self, rmk, pad = None, **kargs):
        align = self.sect_top_align
        sect_top = rmk.accessable_top
        align_top = rmk.realign(align, 0, pad)
        if hasattr(self, '_sect_setinfo'):
            setinfo, sidirty = self._repack_setinfo(
                rmk, self._sect_setinfo, pad = pad, **kargs)
            rmk.set_info(*setinfo)
            rmk._sect_setinfo_dirty = sidirty
        rmk.parse_size(sect_top, align)
        rmk.parse()

    def _repack_with(self, tab, can_extend = False, **kargs):
        dirty = False
        if 'top' in tab and isinstance(tab['top'], int):
            dtop = tab['top']
            dirty = True
        else:
            dtop = None
        if 'dirty' in tab and tab['dirty']:
            dirty = True
        rmk = self.repack_copy(dtop)
        for ofs, bs in tab.items():
            if not isinstance(ofs, int):
                continue
            if not ( 0 <= ofs and
                (can_extend or ofs < rmk.accessable_top - len(bs) + 1) ):
                raise ValueError(f'dest offset not in sect: 0x{ofs:x}')
            rmk.WBYTES(bs, ofs)
            dirty = True
        if dirty:
            return rmk, True
        else:
            return self, False

    def repack_with(self, tab, *args, pad = None, rpkctx = None, **kargs):
        ipad = self._repack_pad()
        if ipad is None:
            ipad = pad
        opad = pad
        if opad is None:
            opad = ipad
        nrpkctx = {}
        rmk, dirty = self._repack_with(tab, *args, pad = ipad, rpkctx = nrpkctx, **kargs)
        if not dirty:
            return rmk, False
        self._repack_end(rmk, *args, pad = opad, rpkctx = nrpkctx, **kargs)
        return rmk, True

# ===============
#      tabs
# ===============

class c_sect_tab(c_sect):
    
    _TAB_WIDTH = 1
    _TAB_BASEOFS = 0
    
    @property
    def sect_align(self):
        wd = self._TAB_WIDTH
        if wd % 4 == 0:
            a = 4
        elif wd % 2 == 0:
            a = 2
        else:
            a = 1
        return max(self._SECT_ALIGN, a)
    
    @property
    def has_tsize(self):
        return hasattr(self, 'tsize') and self.tsize < INF
    
    @property
    def tab_top(self):
        return self.tsize * self._TAB_WIDTH + self._TAB_BASEOFS if self.tsize < INF else None
    
    def parse_size(self, top_ofs, top_align_width):
        has_tsize = self.has_tsize
        if top_ofs is None and has_tsize:
            top_ofs = self.tsize * self._TAB_WIDTH + self._TAB_BASEOFS
        super().parse_size(top_ofs, top_align_width)
        if not has_tsize:
            if top_ofs is None:
                self.tsize = INF
            else:
                self.tsize = (top_ofs - self._TAB_BASEOFS) // self._TAB_WIDTH

    def tbase(self, idx):
        return idx * self._TAB_WIDTH + self._TAB_BASEOFS

    def entry_edge(self, ofs):
        return aligndown(ofs, self._TAB_WIDTH), alignup(ofs, self._TAB_WIDTH)

    def _repack_head(self, tinfo):
        if self._TAB_BASEOFS > 0:
            return self.repack_copy(self._TAB_BASEOFS), False
        else:
            return None, False

    def _rewrite_entry(self, rmk, idx, ofs, ent):
        rmk.writeval(ent, ofs, self._TAB_WIDTH)
    
    def _repack_tab(self, ents, can_extend = False):
        rmk = c_mark(bytearray(), 0)
        ewd = self._TAB_WIDTH
        dirty = False
        for si, ent in enumerate(ents):
            sofs = self.tbase(si)
            if ent is None:
                if si >= self.tsize:
                    raise ValueError(f'invalid tidx: {si}/{self.tsize - 1}')
                ent = self.readval(sofs, ewd, False)
                rmk.writeval(ent, sofs, ewd)
            else:
                if not can_extend and si >= self.tsize:
                    raise ValueError(f'invalid tidx: {si}/{self.tsize - 1}')
                self._rewrite_entry(rmk, si, sofs, ent)
                dirty = True
        if self._TAB_BASEOFS > 0:
            rmk = rmk.sub(self._TAB_BASEOFS)
        return rmk, dirty, None

    def _repack_with(self, tab, can_extend = False, **kargs):
        if not tab:
            return self, False
        dirty = False
        ents = []
        isdict = isinstance(tab, dict)
        if isdict:
            eidxs = [v for v in tab if isinstance(v, int)]
            eidxs.append(self.tsize - 1)
            elen = max(eidxs) + 1
            tlen = -1
            if 'top' in tab:
                elen = min(tab['top'], elen)
                if elen != self.tsize:
                    dirty = True
        else:
            tlen = len(tab)
            elen = max(len(tab), self.tsize)
        for i in range(elen):
            ent = None
            if isdict and i in tab or i < tlen:
                ent = tab[i]
            ents.append(ent)
        tmk, sdirty, tinfo = self._repack_tab(ents, can_extend)
        if sdirty:
            dirty = True
        hmk, sdirty = self._repack_head(tinfo)
        if sdirty:
            dirty = True
        if not dirty:
            return self, False
        rmk = self.repack_copy(0)
        if hmk:
            rmk.concat(hmk)
        rmk.concat(tmk)
        return rmk, dirty

def tabitm(ofs = 0):
    def _mod(mth):
        def _wrap(self, idx, *args, **kargs):
            bs = self.tbase(idx)
            return mth(self, bs + ofs, *args, **kargs)
        return _wrap
    return _mod

def tabkey(key, nochk_ovfl = False):
    mn = 'get_' + key
    def _mod(cls):
        def _getkey(self, k):
            if not nochk_ovfl and k >= self.tsize:
                raise IndexError('overflow')
            if hasattr(self, '_tab_cch'):
                cch = self._tab_cch
            else:
                cch = {}
                self._tab_cch = cch
            if k in cch:
                val = cch[k]
            else:
                val = getattr(self, mn)(k)
                if val is None and nochk_ovfl:
                    raise KeyError(f'no key: {k}')
                cch[k] = val
            return val
        cls.__getitem__ = _getkey
        return cls
    return _mod

@tabkey('ref')
class c_sect_tab_ref(c_sect_tab):
    
    @staticmethod
    def _TAB_REF_CLS():
        return c_sect
    
    @tabitm()
    def get_entry(self, ofs):
        return self.readval(ofs, self._TAB_WIDTH, False)

    @property
    def last_idx(self):
        try:
            return self._last_idx
        except:
            pass
        _last_idx = 0
        _last_ofs = 0
        for i in range(self.tsize):
            sofs = self.get_entry(i)
            if sofs >= _last_ofs:
                _last_ofs = sofs
                _last_idx = i
        self._last_idx = _last_idx
        return _last_idx

    @property
    def last_idxs(self):
        try:
            return self._last_idxs
        except:
            pass
        _last_idxs = []
        _last_ofs = 0
        for i in range(self.tsize):
            sofs = self.get_entry(i)
            if sofs == _last_ofs:
                _last_idxs.append(i)
            elif sofs > _last_ofs:
                _last_ofs = sofs
                _last_idxs = [i]
        self._last_idxs = _last_idxs
        return _last_idxs

    def _is_last(self, idx):
        return idx in self.last_idxs

    def _ref_top_nondeterm(self, idx):
        return self._sect_top_nondeterm and self._is_last(idx)

    def _init_ref(self, sub, idx, ofs):
        try:
            top_ofs = self._tab_ref_size[idx]
        except:
            top_ofs = None
        if isinstance(sub, c_sect_tab_ref_sub):
            sub.set_sub_offset(ofs)
        if self._is_last(idx):
            top_align = (1, self.sect_top_align)
        else:
            top_align = sub.sect_align
        sub.parse_size(top_ofs, top_align)
        if self._ref_top_nondeterm(idx):
            sub.set_nondeterm()
        sub.parse()

    @property
    def sect_top(self):
        if not self._sect_top is None:
            return self._sect_top
        if not self.tsize:
            return None
        lst_sub = self[self.last_idx]
        lst_top = lst_sub.sect_top
        if lst_top is None:
            return None
        real_top = lst_sub.real_offset - self.real_offset + lst_top
        self.set_real_top(real_top)
        return self._sect_top

    def refresh_sect_top(self):
        otop = self._sect_top
        self._sect_top = None
        ntop = self.sect_top
        if ntop is None:
            self._sect_top = otop

    @property
    def sect_top_least(self):
        sect_top = self.sect_top
        if not sect_top is None:
            return sect_top
        if not self.tsize:
            return None
        lst_sub = self[self.last_idx]
        return lst_sub.real_offset - self.real_offset + lst_sub.sect_top_least
    
    def _get_ref(self, idx, setinfo = None):
        ofs = self.get_entry(idx)
        if not ofs:
            return None
        clss = self._TAB_REF_CLS()
        if isinstance(clss, list):
            first_err = None
            for cls in clss:
                sub = self.sub(ofs, cls = cls)
                try:
                    self._init_ref(sub, idx, ofs)
                    break
                except ValueError as ex:
                    if first_err is None:
                        first_err = ex
            else:
                assert(first_err)
                raise first_err
        else:
            sub = self.sub(ofs, cls = clss)
            if not setinfo is None:
                sub.set_info(*setinfo)
            self._init_ref(sub, idx, ofs)
        return sub

    def get_ref(self, idx):
        return self._get_ref(idx, None)

    @property
    def _tab_acs_top(self):
        return self.accessable_top

    def _guess_size(self, top_ofs, upd_sz):
        assert(upd_sz or self.tsize < INF)
        cur_ent = 0
        ofs_min = INF
        ofs_ord = []
        ofs_sort = set()
        acs_top = self._tab_acs_top
        while cur_ent < self.tsize:
            ofs = self.get_entry(cur_ent)
            if ofs < 0:
                raise ValueError('invalid ref tab: tab entry not in range')
            skip = (ofs == 0)
            if (self.tbase(cur_ent) == ofs_min or
                (not top_ofs is None and ofs == top_ofs) or
                # all F entry is invalid and last
                (ofs == (1 << self._TAB_WIDTH * 8) - 1)):
                if upd_sz:
                    self.tsize = cur_ent
                    break
                else:
                    skip = True
            elif (self.tbase(cur_ent) > ofs_min or
                ofs >= acs_top or
                (not top_ofs is None and ofs > top_ofs) ):
                raise ValueError('invalid ref tab: tab entry not in range')
            cur_ent += 1
            if 0 < ofs < ofs_min:
                ofs_min = ofs
            ofs_ord.append(ofs)
            if not skip:
                ofs_sort.add(ofs)
        if self.tsize == 0:
            return []
        if not ofs_sort:
            raise ValueError('invalid ref tab: empty entries')
        ofs_sort = sorted(ofs_sort)
        rslt = []
        for ofs in ofs_ord:
            if ofs == 0:
                rslt.append(0)
                continue
            i = ofs_sort.index(ofs)
            try:
                nxt_ofs = ofs_sort[i+1]
            except:
                nxt_ofs = top_ofs
            try:
                sz = nxt_ofs - ofs
            except:
                sz = None
            rslt.append(sz)
        return rslt

    def parse_size(self, top_ofs, top_align_width):
        super().parse_size(top_ofs, top_align_width)
        self._tab_ref_size = self._guess_size(top_ofs, True)

    def _iter_item(self, path, skiprep, refresh):
        wkofs = {}
        for i, sub in enumerate(self):
            npath = path + [i]
            if skiprep and sub:
                sofs = sub.real_offset
                if sofs in wkofs:
                    yield npath, wkofs[sofs]
                    continue
                wkofs[sofs] = npath
            if isinstance(sub, c_sect_tab_ref):
                yield from sub._iter_item(npath, skiprep, refresh)
            else:
                yield npath, sub
        if refresh:
            self.refresh_sect_top()

    def iter_item(self, skiprep = False, refresh = False):
        yield from self._iter_item([], skiprep, refresh)

    def _iter_content(self):
        yield from self

    def _repack_content(self, tab, base, pad, **kargs):
        mtab = {}
        maxsi = -1
        for idxp, val in tab.items():
            si = idxp[0]
            sidxp = idxp[1:]
            if si > maxsi:
                maxsi = si
            if not sidxp:
                if si in mtab:
                    raise ValueError(f'dumplicate repack tab index: {si}')
                mtab[si] = val
                continue
            if not si in mtab:
                stab = {}
                mtab[si] = stab
            elif isinstance(mtab[si], dict):
                stab = mtab[si]
            else:
                raise ValueError(f'dumplicate repack tab index: {idxp}/{si}')
            stab[sidxp] = val
        rtsize = max(maxsi+1, self.tsize)
        def itr_pck():
            for si, subsect in enumerate(self._iter_content()):
                schr = subsect.real_offset if subsect else None
                dval = mtab[si] if si in mtab else None
                yield schr, subsect, dval
            if maxsi >= self.tsize:
                for si in range(self.tsize, maxsi+1):
                    if si in mtab:
                        subsect = self[0]
                        cls = self._TAB_REF_CLS()
                        if isinstance(cls, list):
                            cls = cls[0]
                        subsect = self.sub(ofs, cls = cls)
                        yield None, subsect, mtab[si]
                    else:
                        yield None, None, None
        cbase = alignup(self._TAB_WIDTH * rtsize + self._TAB_BASEOFS + base, self.sect_align)
        rmks, ents, rlen, dirty = self.repack_compact(itr_pck(), cbase, pad, **kargs)
        if not dirty:
            return None, None
        cmk = c_mark(bytearray(), 0)
        for rmk in rmks:
            if not rmk is None:
                cmk.concat(rmk)
        assert cmk.accessable_top == rlen
        return cmk, ents

    def _rewrite_entry(self, rmk, idx, ofs, ent):
        dofs, dlen = ent
        super()._rewrite_entry(rmk, idx, ofs, dofs)

    def _repack_with(self, tab, pad = None, **kargs):
        cmk, ents = self._repack_content(tab, 0, pad, **kargs)
        if cmk is None:
            return self, False
        # dirty is always True after here
        tmk, sdirty, tinfo = self._repack_tab(ents, True)
        hmk, sdirty = self._repack_head(tinfo)
        rmk = self.repack_copy(0)
        if hmk:
            rmk.concat(hmk)
        rmk.concat(tmk)
        rmk.concat(cmk)
        return rmk, True

class c_sect_tab_ref_sub(c_sect_tab_ref):
    def set_sub_offset(self, ofs):
        self._tab_ref_sub_offset = ofs
    def get_entry(self, idx):
        return super().get_entry(idx) - self._tab_ref_sub_offset
    def _repack_end(self, rmk, base, **kargs):
        rmk.set_sub_offset(base)
        super()._repack_end(rmk)
    def _repack_with(self, tab, base, **kargs):
        cmk, ents = self._repack_content(tab, base, **kargs)
        if cmk is None:
            return self, False
        rmk = self.repack_copy(0)
        ewd = self._TAB_WIDTH
        ebs = self._TAB_BASEOFS
        for si, ent in enumerate(ents):
            rmk.writeval(ent, si * ewd + ebs, ewd)
        rmk.concat(cmk)
        return rmk, True

class c_sect_tab_ref_addr(c_sect_tab_ref):
    
    _TAB_WIDTH = 4
    
    def set_info(self, host, tlen, hole_idxs = None, ignore_invalid_ptr = False):
        self._tab_ref_host = host
        self.tsize = tlen
        if hole_idxs is None:
            hole_idxs = []
        self._tab_hole_idxs = hole_idxs
        self._tab_ref_addr_ignore_invalid_ptr = ignore_invalid_ptr
        
    def _ref_top_nondeterm(self, idx):
        return True

    @property
    def _tab_acs_top(self):
        return self._tab_ref_host.accessable_top
    
    def get_entry(self, idx):
        addr = super().get_entry(idx)
        if addr:
            ofs = self._tab_ref_host.aot(addr, 'ao')
            if self._tab_ref_addr_ignore_invalid_ptr and not self.in_sect(ofs):
                ofs = 0
        else:
            ofs = 0
        return ofs
    
    def get_ref(self, idx):
        ofs = self.get_entry(idx)
        if ofs:
            ref = self._tab_ref_host.sub(ofs, cls = self._TAB_REF_CLS())
            self._init_ref(ref, idx, ofs)
        else:
            ref = None
        return ref
    
    def parse_size(self, top_ofs, top_align_width):
        super(c_sect_tab, self).parse_size(top_ofs, top_align_width)
        tbsz = self._guess_size(top_ofs, False)
        for i in self._tab_hole_idxs:
            if i < len(tbsz):
                tbsz[i] = None
        self._tab_ref_size = tbsz
        self.set_nondeterm()

    def _repack_end(self, rmk, base, **kargs):
        rmk.set_info(rmk, self.tsize,
            self._tab_hole_idxs.copy())
        super()._repack_end(rmk)

    def _repack_with(self, tab, base, **kargs):
        abase = self._tab_ref_host.aot(base, 'oa')
        cmk, ents = self._repack_content(tab, abase, **kargs)
        if cmk is None:
            return self, False
        rmk = type(self)(bytearray(), base)
        ewd = self._TAB_WIDTH
        ebs = self._TAB_BASEOFS
        for si, ent in enumerate(ents):
            rmk.writeval(ent, si * ewd + ebs, ewd)
        rmk.concat(cmk)
        return rmk, True

def meta_c_sect_tab_flex(ent_fmt, alt_ptrs = None):
    @tabkey('entry')
    class c_sect_tab_flex(c_sect_tab):
        _TAB_WIDTH = sum(v[1] for v in ent_fmt)
        _TAB_ALT_PTRS = tuple(alt_ptrs) if alt_ptrs else None
        def set_info(self, tlen):
            self.tsize = tlen
        @tabitm()
        def get_entry(self, ofs):
            r = {}
            vi = 0
            for nm, vw in ent_fmt:
                if vw > 4:
                    rv = self.BYTES(ofs + vi, vw)
                else:
                    rv = self.readval(ofs + vi, vw, False)
                r[nm] = rv
                vi += vw
            return r
        def _repack_with(self, tab, **kargs):
            rmk = self.repack_copy()
            dirty = False
            for didxs, dent in tab.items():
                if isinstance(didxs, int):
                    ditr = (didxs,)
                else:
                    ditr = range(*didxs)
                for didx in ditr:
                    if not 0 <= didx < self.tsize:
                        report('warning', f'invalid tab index {didx}/{self.tsize}')
                        continue
                    dofs = self.tbase(didx)
                    vi = 0
                    for nm, vw in ent_fmt:
                        if nm in dent:
                            dval = dent[nm]
                            if vw > 4:
                                assert len(dval) == vw
                                rmk.WBYTES(dval, dofs + vi)
                            else:
                                rmk.writeval(dval, dofs + vi, vw)
                            dirty = True
                        vi += vw
            if dirty:
                return rmk, True
            else:
                return self, False
    return c_sect_tab_flex
