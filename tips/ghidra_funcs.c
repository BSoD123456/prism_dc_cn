
/* WARNING: Removing unreachable block (ram,0x8c01ba12) */
/* WARNING: Removing unreachable block (ram,0x8c01c1e6) */
/* WARNING: Removing unreachable block (ram,0x8c01b90a) */
/* WARNING: Removing unreachable block (ram,0x8c01c162) */
/* WARNING: Removing unreachable block (ram,0x8c01baac) */
/* WARNING: Removing unreachable block (ram,0x8c01b9e4) */
/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_8c01b842_maybe_parse_script(void)

{
  int iVar1;
  int *piVar2;
  undefined4 uVar3;
  uint uVar4_cur_cmd;
  int *extraout_r3;
  int *extraout_r3_00;
  int iVar4;
  int local_18;
  
  local_18 = 0;
  FUN_8c01b530_load_script_bin();
  do {
    while( true ) {
      if (_DAT_8c18e6b4 != 0) {
        return;
      }
      if (local_18 == 1) {
        return;
      }
      if ((_DAT_8c18e484_maybe_script_cmd_idx & 0x80000000) == 0) break;
      local_18 = FUN_8c01c238_maybe_script_syscall();
    }
    iVar1 = *(int *)((_DAT_8c18e484_maybe_script_cmd_idx >> 0x13) * 8 + -0x73c71928);
    if (iVar1 == -1) {
      _DAT_8c18e6b4 = 1;
      _DAT_8c18e6c0 = 0;
      FUN_8c01b6d8(_DAT_8c18e484_maybe_script_cmd_idx >> 0x13);
      _DAT_8c18e6b8 = _DAT_8c18e6b8 + 1;
      return;
    }
    *(int *)(*(int *)(&DAT_8c38e6d0 + iVar1 * 4) * 8 + -0x73c7192c) = _DAT_8c18e6b8;
    iVar4 = _DAT_8c18e488_maybe_script_stack_idx;
    uVar4_cur_cmd =
         *(uint *)((_DAT_8c18e484_maybe_script_cmd_idx & 0x7ffff) * 4 +
                  iVar1 * 0x200000 + -0x73e71930);
    switch(uVar4_cur_cmd >> 0x1b) {
    case 0:
                    /* nop */
      _DAT_8c18e484_maybe_script_cmd_idx = _DAT_8c18e484_maybe_script_cmd_idx + 1;
      break;
    case 1:
                    /* tab[pop1] = stack[2] */
      *(undefined4 *)
       ((*(uint *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c) >> 5) * 4 +
       -0x73c7150c) = *(undefined4 *)((_DAT_8c18e488_maybe_script_stack_idx + 2) * 4 + -0x73c7170c);
      _DAT_8c18e488_maybe_script_stack_idx = _DAT_8c18e488_maybe_script_stack_idx + 1;
      _DAT_8c18e484_maybe_script_cmd_idx = _DAT_8c18e484_maybe_script_cmd_idx + 1;
      break;
    case 2:
                    /* stack[2] = !!stack[2]
                       tab[stack[1].hi] set(stack[2])/clear(!stack[2]) bits by stack[1].lo
                       pop1 */
      if (*(int *)((_DAT_8c18e488_maybe_script_stack_idx + 2) * 4 + -0x73c7170c) == 0) {
        uVar4_cur_cmd =
             ~(1 << (*(uint *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c) & 0x1f)
              ) & *(uint *)((*(uint *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c)
                            >> 5) * 4 + -0x73c7150c);
      }
      else {
        uVar4_cur_cmd =
             1 << (*(uint *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c) & 0x1f) |
             *(uint *)((*(uint *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c) >> 5
                       ) * 4 + -0x73c7150c);
      }
      *(uint *)((*(uint *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c) >> 5) * 4 +
               -0x73c7150c) = uVar4_cur_cmd;
      *(uint *)((_DAT_8c18e488_maybe_script_stack_idx + 2) * 4 + -0x73c7170c) =
           *(int *)((_DAT_8c18e488_maybe_script_stack_idx + 2) * 4 + -0x73c7170c) == 0 ^ 1;
      _DAT_8c18e488_maybe_script_stack_idx = _DAT_8c18e488_maybe_script_stack_idx + 1;
      _DAT_8c18e484_maybe_script_cmd_idx = _DAT_8c18e484_maybe_script_cmd_idx + 1;
      break;
    case 3:
                    /* stack[1] = tab[stack[1].hi] */
      *(undefined4 *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c) =
           *(undefined4 *)
            ((*(uint *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c) >> 5) * 4 +
            -0x73c7150c);
      goto LAB_8c01bade;
    case 4:
                    /* stack[1] = !!(stack[1].lo & tab[stack[1].hi]) */
      *(uint *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c) =
           (1 << (*(uint *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c) & 0x1f) &
           *(uint *)((*(uint *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c) >> 5)
                     * 4 + -0x73c7150c)) == 0 ^ 1;
      _DAT_8c18e484_maybe_script_cmd_idx = _DAT_8c18e484_maybe_script_cmd_idx + 1;
      break;
    case 5:
                    /* push ? */
      *(uint *)(_DAT_8c18e488_maybe_script_stack_idx * 4 + -0x73c7170c) = uVar4_cur_cmd & 0x7ffffff;
      _DAT_8c18e488_maybe_script_stack_idx = _DAT_8c18e488_maybe_script_stack_idx + -1;
LAB_8c01bade:
      _DAT_8c18e484_maybe_script_cmd_idx = _DAT_8c18e484_maybe_script_cmd_idx + 1;
      break;
    case 6:
                    /* pop ? */
      _DAT_8c18e488_maybe_script_stack_idx = _DAT_8c18e488_maybe_script_stack_idx + 1;
      _DAT_8c18e484_maybe_script_cmd_idx = _DAT_8c18e484_maybe_script_cmd_idx + 1;
      break;
    case 7:
                    /* calculate, not calcrate */
      switch(uVar4_cur_cmd & 0x7ffffff) {
      case 0:
                    /* nop */
        break;
      case 1:
                    /* stack[2] = stack[2] + stack[1]
                       pop 1 */
        piVar2 = (int *)&DAT_8c18e488_maybe_script_stack_idx;
        *(int *)((_DAT_8c18e488_maybe_script_stack_idx + 2) * 4 + -0x73c7170c) =
             *(int *)((_DAT_8c18e488_maybe_script_stack_idx + 2) * 4 + -0x73c7170c) +
             *(int *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c);
        iVar1 = _DAT_8c18e488_maybe_script_stack_idx + 1;
        goto LAB_8c01bc60;
      case 2:
                    /* stack[2] - stack[1] */
        *(int *)((_DAT_8c18e488_maybe_script_stack_idx + 2) * 4 + -0x73c7170c) =
             *(int *)((_DAT_8c18e488_maybe_script_stack_idx + 2) * 4 + -0x73c7170c) -
             *(int *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c);
        _DAT_8c18e488_maybe_script_stack_idx = _DAT_8c18e488_maybe_script_stack_idx + 1;
        break;
      case 3:
                    /* stack[2] * stack[1] */
        *(int *)((_DAT_8c18e488_maybe_script_stack_idx + 2) * 4 + -0x73c7170c) =
             *(int *)((_DAT_8c18e488_maybe_script_stack_idx + 2) * 4 + -0x73c7170c) *
             *(int *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c);
        goto LAB_8c01bee2;
      case 4:
                    /* stack[2] // stack[1] */
        uVar3 = FUN_8c01eeb0();
        piVar2 = extraout_r3;
        goto LAB_8c01bc3c;
      case 5:
                    /* stack[2] % stack[1] */
        uVar3 = FUN_8c01f00c();
        piVar2 = extraout_r3_00;
LAB_8c01bc3c:
        *(undefined4 *)((iVar4 + 2) * 4 + -0x73c7170c) = uVar3;
        *piVar2 = *piVar2 + 1;
        break;
      case 6:
                    /* -stack[1] */
        piVar2 = (int *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c);
        iVar1 = -*(int *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c);
LAB_8c01bc60:
        *piVar2 = iVar1;
        break;
      case 7:
                    /* stack[2] == stack[1] */
        *(uint *)((_DAT_8c18e488_maybe_script_stack_idx + 2) * 4 + -0x73c7170c) =
             (uint)(*(int *)((_DAT_8c18e488_maybe_script_stack_idx + 2) * 4 + -0x73c7170c) ==
                   *(int *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c));
        _DAT_8c18e488_maybe_script_stack_idx = _DAT_8c18e488_maybe_script_stack_idx + 1;
        break;
      case 8:
                    /* stack[1] < stack[2] */
        *(uint *)((_DAT_8c18e488_maybe_script_stack_idx + 2) * 4 + -0x73c7170c) =
             (uint)(*(int *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c) <
                   *(int *)((_DAT_8c18e488_maybe_script_stack_idx + 2) * 4 + -0x73c7170c));
        goto LAB_8c01bee2;
      case 9:
                    /* stack[1] <= stack[2] */
        *(uint *)((_DAT_8c18e488_maybe_script_stack_idx + 2) * 4 + -0x73c7170c) =
             (uint)(*(int *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c) <=
                   *(int *)((_DAT_8c18e488_maybe_script_stack_idx + 2) * 4 + -0x73c7170c));
        _DAT_8c18e488_maybe_script_stack_idx = _DAT_8c18e488_maybe_script_stack_idx + 1;
        break;
      case 10:
                    /* stack[1] > stack[2] */
        *(uint *)((_DAT_8c18e488_maybe_script_stack_idx + 2) * 4 + -0x73c7170c) =
             *(int *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c) <=
             *(int *)((_DAT_8c18e488_maybe_script_stack_idx + 2) * 4 + -0x73c7170c) ^ 1;
        goto LAB_8c01bee2;
      case 0xb:
                    /* stack[1] >= stack[2] */
        *(uint *)((_DAT_8c18e488_maybe_script_stack_idx + 2) * 4 + -0x73c7170c) =
             *(int *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c) <
             *(int *)((_DAT_8c18e488_maybe_script_stack_idx + 2) * 4 + -0x73c7170c) ^ 1;
        _DAT_8c18e488_maybe_script_stack_idx = _DAT_8c18e488_maybe_script_stack_idx + 1;
        break;
      case 0xc:
                    /* stack[2] != stack[1] */
        *(uint *)((_DAT_8c18e488_maybe_script_stack_idx + 2) * 4 + -0x73c7170c) =
             *(int *)((_DAT_8c18e488_maybe_script_stack_idx + 2) * 4 + -0x73c7170c) ==
             *(int *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c) ^ 1;
        goto LAB_8c01bee2;
      case 0xd:
                    /* stack[2] && stack[1] */
        if ((*(int *)((_DAT_8c18e488_maybe_script_stack_idx + 2) * 4 + -0x73c7170c) == 0) ||
           (*(int *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c) == 0)) {
          uVar3 = 0;
        }
        else {
          uVar3 = 1;
        }
        *(undefined4 *)((_DAT_8c18e488_maybe_script_stack_idx + 2) * 4 + -0x73c7170c) = uVar3;
        _DAT_8c18e488_maybe_script_stack_idx = _DAT_8c18e488_maybe_script_stack_idx + 1;
        break;
      case 0xe:
                    /* stack[2] || stack[1] */
        if ((*(int *)((_DAT_8c18e488_maybe_script_stack_idx + 2) * 4 + -0x73c7170c) == 0) &&
           (*(int *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c) == 0)) {
          uVar3 = 0;
        }
        else {
          uVar3 = 1;
        }
        *(undefined4 *)((_DAT_8c18e488_maybe_script_stack_idx + 2) * 4 + -0x73c7170c) = uVar3;
        _DAT_8c18e488_maybe_script_stack_idx = _DAT_8c18e488_maybe_script_stack_idx + 1;
        break;
      case 0xf:
                    /* stack[2] & stack[1] */
        *(uint *)((_DAT_8c18e488_maybe_script_stack_idx + 2) * 4 + -0x73c7170c) =
             *(uint *)((_DAT_8c18e488_maybe_script_stack_idx + 2) * 4 + -0x73c7170c) &
             *(uint *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c);
        goto LAB_8c01bee2;
      case 0x10:
                    /* stack[2] | stack[1] */
        *(uint *)((_DAT_8c18e488_maybe_script_stack_idx + 2) * 4 + -0x73c7170c) =
             *(uint *)((_DAT_8c18e488_maybe_script_stack_idx + 2) * 4 + -0x73c7170c) |
             *(uint *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c);
        _DAT_8c18e488_maybe_script_stack_idx = _DAT_8c18e488_maybe_script_stack_idx + 1;
        break;
      case 0x11:
                    /* stack[2] ^ stack[1] */
        *(uint *)((_DAT_8c18e488_maybe_script_stack_idx + 2) * 4 + -0x73c7170c) =
             *(uint *)((_DAT_8c18e488_maybe_script_stack_idx + 2) * 4 + -0x73c7170c) ^
             *(uint *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c);
        goto LAB_8c01bee2;
      case 0x12:
                    /* stack[2] << stack[1].lo or >> ~stack[1].lo + 1 */
        iVar1 = *(int *)((_DAT_8c18e488_maybe_script_stack_idx + 2) * 4 + -0x73c7170c);
        uVar4_cur_cmd = *(uint *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c);
        if ((int)uVar4_cur_cmd < 0) {
          iVar1 = iVar1 >> (~uVar4_cur_cmd & 0x1f) + 1;
        }
        else {
          iVar1 = iVar1 << (uVar4_cur_cmd & 0x1f);
        }
        *(int *)((_DAT_8c18e488_maybe_script_stack_idx + 2) * 4 + -0x73c7170c) = iVar1;
        _DAT_8c18e488_maybe_script_stack_idx = _DAT_8c18e488_maybe_script_stack_idx + 1;
        break;
      case 0x13:
                    /* stack[2] >> ~stack[1].lo + 1 or << stack[1].lo */
        iVar4 = *(int *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c);
        iVar1 = *(int *)((_DAT_8c18e488_maybe_script_stack_idx + 2) * 4 + -0x73c7170c);
        uVar4_cur_cmd = -iVar4;
        if (iVar4 < 1) {
          iVar1 = iVar1 << (uVar4_cur_cmd & 0x1f);
        }
        else {
          iVar1 = iVar1 >> (~uVar4_cur_cmd & 0x1f) + 1;
        }
        *(int *)((_DAT_8c18e488_maybe_script_stack_idx + 2) * 4 + -0x73c7170c) = iVar1;
LAB_8c01bee2:
        _DAT_8c18e488_maybe_script_stack_idx = _DAT_8c18e488_maybe_script_stack_idx + 1;
        break;
      default:
        FUN_8c010510(s_ipt_coding_error(calcrate).:%08x_8c02460c,_DAT_8c18e484_maybe_script_cmd_idx)
        ;
        thunk_FUN_8c0104a4(0xffffffff);
      }
      _DAT_8c18e484_maybe_script_cmd_idx = _DAT_8c18e484_maybe_script_cmd_idx + 1;
      break;
    case 8:
                    /* jump condi */
      uVar4_cur_cmd = uVar4_cur_cmd & 0x7ffffff;
      if (uVar4_cur_cmd == 0x14) {
                    /* pop dest */
        _DAT_8c18e484_maybe_script_cmd_idx =
             *(uint *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c);
        _DAT_8c18e488_maybe_script_stack_idx = _DAT_8c18e488_maybe_script_stack_idx + 1;
      }
      else if (uVar4_cur_cmd == 0x15) {
                    /* pop2 condi -> 0: nop, !0: pop dest */
        if (*(int *)((_DAT_8c18e488_maybe_script_stack_idx + 2) * 4 + -0x73c7170c) == 0) {
          _DAT_8c18e484_maybe_script_cmd_idx = _DAT_8c18e484_maybe_script_cmd_idx + 1;
        }
        else {
          _DAT_8c18e484_maybe_script_cmd_idx =
               *(uint *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c);
        }
        _DAT_8c18e488_maybe_script_stack_idx = _DAT_8c18e488_maybe_script_stack_idx + 2;
      }
      else if (uVar4_cur_cmd == 0x16) {
                    /* pop2 condi -> 0: pop dest, !0: nop */
        if (*(int *)((_DAT_8c18e488_maybe_script_stack_idx + 2) * 4 + -0x73c7170c) == 0) {
          _DAT_8c18e484_maybe_script_cmd_idx =
               *(uint *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c);
        }
        else {
          _DAT_8c18e484_maybe_script_cmd_idx = _DAT_8c18e484_maybe_script_cmd_idx + 1;
        }
        _DAT_8c18e488_maybe_script_stack_idx = _DAT_8c18e488_maybe_script_stack_idx + 2;
      }
      else {
        FUN_8c010510(s_ipt_coding_error(jump).:%08x_8c024630,_DAT_8c18e484_maybe_script_cmd_idx);
        thunk_FUN_8c0104a4(0xffffffff);
      }
      break;
    case 9:
                    /* call
                       iv-push cmd_idx
                       cmd_idx = pop1 */
      iVar1 = _DAT_8c18e490_maybe_script_invoke_idx * 4;
      _DAT_8c18e490_maybe_script_invoke_idx = _DAT_8c18e490_maybe_script_invoke_idx + -1;
      *(uint *)(iVar1 + -0x73c7190c) = _DAT_8c18e484_maybe_script_cmd_idx + 1;
      _DAT_8c18e484_maybe_script_cmd_idx =
           *(uint *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c);
      goto LAB_8c01c06c;
    case 10:
                    /* syscall with (pop1 << 8) | 0x80000000 */
      iVar1 = _DAT_8c18e490_maybe_script_invoke_idx * 4;
      _DAT_8c18e490_maybe_script_invoke_idx = _DAT_8c18e490_maybe_script_invoke_idx + -1;
      *(uint *)(iVar1 + -0x73c7190c) = _DAT_8c18e484_maybe_script_cmd_idx + 1;
      _DAT_8c18e484_maybe_script_cmd_idx =
           *(int *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c) << 8 | 0x80000000;
      _DAT_8c18e488_maybe_script_stack_idx = _DAT_8c18e488_maybe_script_stack_idx + 1;
      break;
    case 0xb:
                    /* return */
      _DAT_8c18e484_maybe_script_cmd_idx =
           *(uint *)((_DAT_8c18e490_maybe_script_invoke_idx + 1) * 4 + -0x73c7190c);
      _DAT_8c18e490_maybe_script_invoke_idx = _DAT_8c18e490_maybe_script_invoke_idx + 1;
      break;
    case 0xc:
                    /* call (as 9) for text */
      iVar1 = _DAT_8c18e490_maybe_script_invoke_idx * 4;
      _DAT_8c18e490_maybe_script_invoke_idx = _DAT_8c18e490_maybe_script_invoke_idx + -1;
      *(uint *)(iVar1 + -0x73c7190c) = _DAT_8c18e484_maybe_script_cmd_idx + 1;
      _DAT_8c18e484_maybe_script_cmd_idx =
           *(uint *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c);
LAB_8c01c06c:
      _DAT_8c18e488_maybe_script_stack_idx = _DAT_8c18e488_maybe_script_stack_idx + 1;
      break;
    case 0xd:
                    /* sub glb-counter ? maybe heap alloc */
      uVar4_cur_cmd = -((uVar4_cur_cmd & 0x7ffffff) >> 5);
      goto LAB_8c01c0cc;
    case 0xe:
                    /* add glb-counter ? maybe heap free */
      uVar4_cur_cmd = (uVar4_cur_cmd & 0x7ffffff) >> 5;
LAB_8c01c0cc:
      _DAT_8c18e48c_maybe_script_some_glb_counter =
           _DAT_8c18e48c_maybe_script_some_glb_counter + uVar4_cur_cmd;
      _DAT_8c18e484_maybe_script_cmd_idx = _DAT_8c18e484_maybe_script_cmd_idx + 1;
      break;
    case 0xf:
                    /* push glb-counter ? maybe push heap point for syscall */
      *(int *)(_DAT_8c18e488_maybe_script_stack_idx * 4 + -0x73c7170c) =
           _DAT_8c18e48c_maybe_script_some_glb_counter << 5;
      _DAT_8c18e488_maybe_script_stack_idx = _DAT_8c18e488_maybe_script_stack_idx + -1;
      _DAT_8c18e484_maybe_script_cmd_idx = _DAT_8c18e484_maybe_script_cmd_idx + 1;
      break;
    case 0x10:
                    /* nop (as 0) */
      _DAT_8c18e484_maybe_script_cmd_idx = _DAT_8c18e484_maybe_script_cmd_idx + 1;
      break;
    case 0x11:
                    /* text string 2-bytes (0x1fff << 0xd + 0x1fff)
                       all1 -> return */
      if ((uVar4_cur_cmd & 0x3ffffff) == 0x3ffffff) {
        if (0xff < _DAT_8c18e6b0_string_buf) {
          FUN_8c010510(s_string_buffer_overflow._8c024650);
          thunk_FUN_8c0104a4(0xffffffff);
        }
        _DAT_8c18e484_maybe_script_cmd_idx =
             *(uint *)((_DAT_8c18e490_maybe_script_invoke_idx + 1) * 4 + -0x73c7190c);
        _DAT_8c18e490_maybe_script_invoke_idx = _DAT_8c18e490_maybe_script_invoke_idx + 1;
      }
      else {
        iVar1 = _DAT_8c18e6b0_string_buf * 2;
        _DAT_8c18e6b0_string_buf = _DAT_8c18e6b0_string_buf + 1;
        *(ushort *)(&DAT_8c18e4b0 + iVar1) = (ushort)uVar4_cur_cmd & 0x1fff;
        uVar4_cur_cmd = uVar4_cur_cmd >> 0xd & 0x1fff;
        if (uVar4_cur_cmd != 0x1fff) {
          iVar1 = _DAT_8c18e6b0_string_buf * 2;
          _DAT_8c18e6b0_string_buf = _DAT_8c18e6b0_string_buf + 1;
          *(short *)(&DAT_8c18e4b0 + iVar1) = (short)uVar4_cur_cmd;
        }
        _DAT_8c18e484_maybe_script_cmd_idx = _DAT_8c18e484_maybe_script_cmd_idx + 1;
      }
      break;
    case 0x12:
                    /* text string hi-1 */
      iVar1 = _DAT_8c18e6b0_string_buf * 2;
      _DAT_8c18e6b0_string_buf = _DAT_8c18e6b0_string_buf + 1;
      *(ushort *)(&DAT_8c18e4b0 + iVar1) = (ushort)uVar4_cur_cmd & 0x1fff | 0x2000;
      uVar4_cur_cmd = uVar4_cur_cmd >> 0xd & 0x1fff;
      if (uVar4_cur_cmd != 0x1fff) {
        iVar1 = _DAT_8c18e6b0_string_buf * 2;
        _DAT_8c18e6b0_string_buf = _DAT_8c18e6b0_string_buf + 1;
        *(ushort *)(&DAT_8c18e4b0 + iVar1) = (ushort)uVar4_cur_cmd | 0x2000;
      }
      _DAT_8c18e484_maybe_script_cmd_idx = _DAT_8c18e484_maybe_script_cmd_idx + 1;
    }
  } while( true );
}




/* WARNING: Removing unreachable block (ram,0x8c01c3e4) */
/* WARNING: Removing unreachable block (ram,0x8c01c40c) */
/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined4 FUN_8c01c238_maybe_script_syscall(void)

{
  undefined4 uVar1;
  uint uVar2;
  int iVar3;
  int iVar4;
  bool bVar5;
  bool bVar6;
  int local_1c;
  undefined4 local_18;
  int local_14;
  uint local_10;
  int local_c;
  
  switch((_DAT_8c18e484_maybe_script_cmd_idx & 0x7fffffff) >> 8) {
  case 0:
    local_10 = *(uint *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c) >> 5;
    if (_DAT_8c18e6b0_string_buf != 0) {
      local_14 = 0;
      while (local_14 < (int)_DAT_8c18e6b0_string_buf) {
        iVar3 = local_14 + 1;
        iVar4 = local_14 * 2;
        local_14 = local_14 + 2;
        *(uint *)(local_10 * 4 + -0x73c7150c) =
             CONCAT22(*(undefined2 *)(&DAT_8c18e4b0 + iVar3 * 2),
                      *(undefined2 *)(&DAT_8c18e4b0 + iVar4));
        local_10 = local_10 + 1;
      }
    }
    if ((int)_DAT_8c18e6b0_string_buf < 0) {
      uVar2 = ~(~_DAT_8c18e6b0_string_buf + 1 & 1) + 1;
    }
    else {
      uVar2 = _DAT_8c18e6b0_string_buf & 1;
    }
    if (uVar2 == 0) {
      *(undefined4 *)(local_10 * 4 + -0x73c7150c) = 0x1fff1fff;
    }
    else {
      *(uint *)((local_10 - 1) * 4 + -0x73c7150c) =
           *(ushort *)((local_10 - 1) * 4 + -0x73c7150c) | 0x1fff0000;
    }
    *(undefined4 *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c) = 0xffffffff;
    FUN_8c018fce();
    local_1c = 1;
    local_18 = 0;
    goto LAB_8c01decc_done;
  case 1:
    local_10 = *(uint *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c) >> 5;
    while( true ) {
      uVar2 = *(uint *)(local_10 * 4 + -0x73c7150c);
      if (((uVar2 >> 0xd & 3) == 0) && ((uVar2 & 0x1fff) == 0x1fff)) break;
      iVar3 = _DAT_8c18e6b0_string_buf * 2;
      _DAT_8c18e6b0_string_buf = _DAT_8c18e6b0_string_buf + 1;
      *(short *)(&DAT_8c18e4b0 + iVar3) = (short)uVar2;
      if (((uVar2 >> 0x1d & 3) == 0) && ((uVar2 >> 0x10 & 0x1fff) == 0x1fff)) break;
      iVar3 = _DAT_8c18e6b0_string_buf * 2;
      _DAT_8c18e6b0_string_buf = _DAT_8c18e6b0_string_buf + 1;
      *(short *)(&DAT_8c18e4b0 + iVar3) = (short)(uVar2 >> 0x10);
      local_10 = local_10 + 1;
    }
    if (0xff < (int)_DAT_8c18e6b0_string_buf) {
      FUN_8c010510(s_string_buffer_overflow._8c024650);
      thunk_FUN_8c0104a4(0xffffffff);
    }
    *(undefined4 *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c) = 0xffffffff;
    goto LAB_8c01c5b4;
  case 2:
    iVar3 = _DAT_8c18e6b0_string_buf * 2;
    _DAT_8c18e6b0_string_buf = _DAT_8c18e6b0_string_buf + 1;
    *(ushort *)(&DAT_8c18e4b0 + iVar3) =
         *(ushort *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c) | 0x2000;
    *(undefined4 *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c) = 0xffffffff;
    if (0xff < (int)_DAT_8c18e6b0_string_buf) {
      FUN_8c010510(s_string_buffer_overflow._8c024650);
      thunk_FUN_8c0104a4(0xffffffff);
    }
    goto LAB_8c01c50a;
  case 3:
    iVar3 = _DAT_8c18e488_maybe_script_stack_idx * 4;
    uVar2 = FUN_8c01f450();
    if ((int)uVar2 < 0) {
      uVar2 = ~(~uVar2 + 1 & 0x7ffffff) + 1;
    }
    else {
      uVar2 = uVar2 & 0x7ffffff;
    }
    *(uint *)(iVar3 + -0x73c7170c) = uVar2;
    _DAT_8c18e488_maybe_script_stack_idx = _DAT_8c18e488_maybe_script_stack_idx + -1;
LAB_8c01c50a:
    local_1c = 1;
    local_18 = 0;
    goto LAB_8c01decc_done;
  case 4:
    iVar3 = FUN_8c018050();
    if ((iVar3 == 0) || (iVar3 = FUN_8c019ace(), iVar3 == 1)) {
      local_1c = 0;
      local_18 = 1;
    }
    else {
      *(undefined4 *)(_DAT_8c18e488_maybe_script_stack_idx * 4 + -0x73c7170c) = 0xffffffff;
      _DAT_8c18e488_maybe_script_stack_idx = _DAT_8c18e488_maybe_script_stack_idx + -1;
      local_1c = 1;
      local_18 = 0;
    }
    goto LAB_8c01decc_done;
  case 5:
    iVar3 = _DAT_8c18e488_maybe_script_stack_idx * 4;
    _DAT_8c18e488_maybe_script_stack_idx = _DAT_8c18e488_maybe_script_stack_idx + -1;
    *(undefined4 *)(iVar3 + -0x73c7170c) = 0xffffffff;
    local_18 = 1;
    local_1c = 1;
    goto LAB_8c01decc_done;
  case 6:
    local_18 = FUN_8c01e89c(&DAT_8c18e484_maybe_script_cmd_idx);
    goto LAB_8c01d5cc_condi_return;
  case 7:
    local_18 = FUN_8c01ea14(&DAT_8c18e484_maybe_script_cmd_idx);
    goto LAB_8c01d5cc_condi_return;
  case 8:
    local_18 = FUN_8c01ea3e(&DAT_8c18e484_maybe_script_cmd_idx);
    goto LAB_8c01d5cc_condi_return;
  case 9:
    iVar3 = _DAT_8c18e488_maybe_script_stack_idx * 4;
    _DAT_8c18e488_maybe_script_stack_idx = _DAT_8c18e488_maybe_script_stack_idx + -1;
    *(undefined4 *)(iVar3 + -0x73c7170c) = _DAT_8c0b8814;
LAB_8c01c5b4:
    local_1c = 1;
    local_18 = 0;
    goto LAB_8c01decc_done;
  case 10:
    iVar3 = _DAT_8c18e488_maybe_script_stack_idx * 4;
    _DAT_8c18e488_maybe_script_stack_idx = _DAT_8c18e488_maybe_script_stack_idx + -1;
    *(undefined4 *)(iVar3 + -0x73c7170c) = _DAT_8c0bcee8;
    break;
  case 0xb:
    FUN_8c0185ea(*(undefined4 *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c));
    *(undefined4 *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c) = 0xffffffff;
    local_1c = 1;
    local_18 = 0;
    goto LAB_8c01decc_done;
  case 0xc:
    uVar2 = _DAT_8c18e484_maybe_script_cmd_idx & 0xff;
    if (uVar2 == 0) {
      _DAT_8c18e48c_maybe_script_some_glb_counter = _DAT_8c18e48c_maybe_script_some_glb_counter + -8
      ;
      *(undefined4 *)(_DAT_8c18e48c_maybe_script_some_glb_counter * 4 + -0x73c7150c) =
           *(undefined4 *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c);
      iVar3 = _DAT_8c18e488_maybe_script_stack_idx + 2;
      _DAT_8c18e488_maybe_script_stack_idx = _DAT_8c18e488_maybe_script_stack_idx + 1;
      *(undefined4 *)((_DAT_8c18e48c_maybe_script_some_glb_counter + 1) * 4 + -0x73c7150c) =
           *(undefined4 *)(iVar3 * 4 + -0x73c7170c);
      iVar3 = _DAT_8c18e488_maybe_script_stack_idx + 2;
      _DAT_8c18e488_maybe_script_stack_idx = _DAT_8c18e488_maybe_script_stack_idx + 1;
      *(undefined4 *)((_DAT_8c18e48c_maybe_script_some_glb_counter + 2) * 4 + -0x73c7150c) =
           *(undefined4 *)(iVar3 * 4 + -0x73c7170c);
      _DAT_8c18e488_maybe_script_stack_idx = _DAT_8c18e488_maybe_script_stack_idx + 1;
      *(undefined4 *)((_DAT_8c18e48c_maybe_script_some_glb_counter + 4) * 4 + -0x73c7150c) = 0;
      _DAT_8c18e484_maybe_script_cmd_idx = (_DAT_8c18e484_maybe_script_cmd_idx & 0xffffff00) + 1;
      local_18 = 0;
      local_1c = 0;
      goto LAB_8c01decc_done;
    }
    if (uVar2 == 1) {
      if (((_DAT_8c18e498 & 0x41) == 0) && ((_DAT_8c18e498 & 0x10) == 0)) {
        uVar1 = 0;
      }
      else {
        uVar1 = 1;
      }
      FUN_8c01904c(1,uVar1);
      FUN_8c0194cc(0);
      if (_DAT_8c0bcf34 == 5) {
        _DAT_8c18e484_maybe_script_cmd_idx = (_DAT_8c18e484_maybe_script_cmd_idx & 0xffffff00) + 2;
      }
      local_1c = 0;
      local_18 = 1;
      goto LAB_8c01decc_done;
    }
    if (uVar2 != 2) {
      if (uVar2 == 3) {
        *(undefined4 *)(_DAT_8c18e488_maybe_script_stack_idx * 4 + -0x73c7170c) = 0xffffffff;
        _DAT_8c18e488_maybe_script_stack_idx = _DAT_8c18e488_maybe_script_stack_idx + -1;
        _DAT_8c18e48c_maybe_script_some_glb_counter =
             _DAT_8c18e48c_maybe_script_some_glb_counter + 8;
        local_1c = 1;
        local_18 = 0;
        _DAT_8c18e498 = (uint)_DAT_8c0bcf54;
      }
      else if (uVar2 == 4) {
        *(uint *)(_DAT_8c18e490_maybe_script_invoke_idx * 4 + -0x73c7190c) =
             (_DAT_8c18e484_maybe_script_cmd_idx & 0xffffff00) + 5;
        _DAT_8c18e490_maybe_script_invoke_idx = _DAT_8c18e490_maybe_script_invoke_idx + -1;
        _DAT_8c18e484_maybe_script_cmd_idx = 0xd27;
        local_18 = 0;
        local_1c = 0;
      }
      else if (uVar2 == 5) {
        _DAT_8c18e488_maybe_script_stack_idx = _DAT_8c18e488_maybe_script_stack_idx + 1;
        _DAT_8c18e484_maybe_script_cmd_idx = (_DAT_8c18e484_maybe_script_cmd_idx & 0xffffff00) + 1;
        local_1c = 0;
        local_18 = 1;
      }
      else {
        FUN_8c010510(s_ipt_exec_coding_error._8c02466c);
        thunk_FUN_8c0104a4(0xffffffff);
      }
      goto LAB_8c01decc_done;
    }
    if (((_DAT_8c0bcf4c & 0x80) != 0) && (_DAT_8c18e4a8 == 1)) {
      FUN_8c0177c0(0x6b);
      bVar5 = _DAT_8c18e4a0 != 1;
      if (bVar5) {
        FUN_8c019b82(*(undefined4 *)
                      ((_DAT_8c18e48c_maybe_script_some_glb_counter + 5) * 4 + -0x73c7150c));
        FUN_8c01a4c4(*(undefined4 *)
                      ((_DAT_8c18e48c_maybe_script_some_glb_counter + 6) * 4 + -0x73c7150c));
        FUN_8c01a4ca(*(undefined4 *)
                      ((_DAT_8c18e48c_maybe_script_some_glb_counter + 7) * 4 + -0x73c7150c));
        FUN_8c018a9e();
        *(undefined4 *)(_DAT_8c18e488_maybe_script_stack_idx * 4 + -0x73c7170c) =
             *(undefined4 *)((_DAT_8c18e48c_maybe_script_some_glb_counter + 3) * 4 + -0x73c7150c);
        _DAT_8c18e488_maybe_script_stack_idx = _DAT_8c18e488_maybe_script_stack_idx + -1;
        FUN_8c01eba2(&DAT_8c18e484_maybe_script_cmd_idx);
      }
      else {
        *(undefined4 *)((_DAT_8c18e48c_maybe_script_some_glb_counter + 3) * 4 + -0x73c7150c) =
             _DAT_8c0bcee8;
        *(undefined4 *)((_DAT_8c18e48c_maybe_script_some_glb_counter + 5) * 4 + -0x73c7150c) =
             _DAT_8c0bd3ac;
        *(undefined4 *)((_DAT_8c18e48c_maybe_script_some_glb_counter + 6) * 4 + -0x73c7150c) =
             _DAT_8c0bd448;
        *(undefined4 *)((_DAT_8c18e48c_maybe_script_some_glb_counter + 7) * 4 + -0x73c7150c) =
             _DAT_8c0bd44c;
        FUN_8c018ad4();
        FUN_8c019b82(0);
        FUN_8c01a4c4(0);
        FUN_8c01a4ca(0);
        *(undefined4 *)(_DAT_8c18e488_maybe_script_stack_idx * 4 + -0x73c7170c) = 0;
        _DAT_8c18e488_maybe_script_stack_idx = _DAT_8c18e488_maybe_script_stack_idx + -1;
        FUN_8c01ea72(&DAT_8c18e484_maybe_script_cmd_idx);
      }
      _DAT_8c18e488_maybe_script_stack_idx = _DAT_8c18e488_maybe_script_stack_idx + 1;
      _DAT_8c18e4a0 = (uint)bVar5;
    }
    if (((_DAT_8c18e4a0 == 1) && (_DAT_8c18e4ac == 1)) && ((_DAT_8c0bcf54 & 0x800) != 0)) {
      FUN_8c0177c0(0x65);
      _DAT_8c18e484_maybe_script_cmd_idx = (_DAT_8c18e484_maybe_script_cmd_idx & 0xffffff00) + 4;
      local_18 = 0;
      local_1c = 0;
      goto LAB_8c01decc_done;
    }
    if ((_DAT_8c18e4a0 != 1) ||
       ((((iVar3 = FUN_8c01947e(), iVar3 == 0 ||
          ((((_DAT_8c0bcf4c & 0x24) == 0 && ((_DAT_8c0bcf4c & 0x41) == 0)) &&
           (iVar3 = FUN_8c016652(), iVar3 == 0)))) &&
         ((((_DAT_8c0bcf54 & 0x10) == 0 ||
           (((*(uint *)((_DAT_8c18e48c_maybe_script_some_glb_counter + 2) * 4 + -0x73c7150c) & 1) ==
             0 && ((_DAT_8c38eca0 & 2) == 0)))) &&
          ((*(int *)((_DAT_8c18e48c_maybe_script_some_glb_counter + 4) * 4 + -0x73c7150c) <
            *(int *)((_DAT_8c18e48c_maybe_script_some_glb_counter + 1) * 4 + -0x73c7150c) ||
           (*(int *)((_DAT_8c18e48c_maybe_script_some_glb_counter + 1) * 4 + -0x73c7150c) < 1))))))
        && ((iVar3 = FUN_8c0173c6(), iVar3 != 1 ||
            (*(int *)((_DAT_8c18e48c_maybe_script_some_glb_counter + 1) * 4 + -0x73c7150c) != -1))))
       )) {
      iVar3 = (_DAT_8c18e48c_maybe_script_some_glb_counter + 4) * 4;
      *(int *)(iVar3 + -0x73c7150c) = *(int *)(iVar3 + -0x73c7150c) + 1;
      FUN_8c01904c(1,_DAT_8c0bcf4c & 0x41);
      local_c = 0;
      if ((_DAT_8c0bcf54 & 0x9008) != 0) {
        local_c = -1;
      }
      if ((_DAT_8c0bcf54 & 0x6002) != 0) {
        local_c = local_c + 1;
      }
      FUN_8c0194cc(local_c);
      local_1c = 0;
      local_18 = 1;
      goto LAB_8c01decc_done;
    }
    *(undefined4 *)
     (((*(uint *)(_DAT_8c18e48c_maybe_script_some_glb_counter * 4 + -0x73c7150c) >> 5) + 1) * 4 +
     -0x73c7150c) = 0;
    *(undefined4 *)
     (((*(uint *)(_DAT_8c18e48c_maybe_script_some_glb_counter * 4 + -0x73c7150c) >> 5) + 2) * 4 +
     -0x73c7150c) = 0;
    *(undefined4 *)
     (((*(uint *)(_DAT_8c18e48c_maybe_script_some_glb_counter * 4 + -0x73c7150c) >> 5) + 3) * 4 +
     -0x73c7150c) =
         *(undefined4 *)((_DAT_8c18e48c_maybe_script_some_glb_counter + 4) * 4 + -0x73c7150c);
    if ((*(int *)((_DAT_8c18e48c_maybe_script_some_glb_counter + 4) * 4 + -0x73c7150c) <
         *(int *)((_DAT_8c18e48c_maybe_script_some_glb_counter + 1) * 4 + -0x73c7150c)) ||
       (*(int *)((_DAT_8c18e48c_maybe_script_some_glb_counter + 1) * 4 + -0x73c7150c) < 1)) {
      iVar3 = FUN_8c0173c6();
      if ((iVar3 == 1) &&
         (*(int *)((_DAT_8c18e48c_maybe_script_some_glb_counter + 1) * 4 + -0x73c7150c) == -1)) {
        iVar3 = ((*(uint *)(_DAT_8c18e48c_maybe_script_some_glb_counter * 4 + -0x73c7150c) >> 5) + 2
                ) * 4;
        *(uint *)(iVar3 + -0x73c7150c) = *(uint *)(iVar3 + -0x73c7150c) | 8;
      }
      else {
        if ((_DAT_8c0bcf4c & 0x41) == 0) {
          if ((_DAT_8c0bcf4c & 0x24) == 0) {
            iVar3 = FUN_8c016652();
            if (iVar3 != 0) {
              iVar3 = *(int *)(_DAT_8c18e48c_maybe_script_some_glb_counter * 4 + -0x73c7150c) * 4;
              *(uint *)(iVar3 + -0x73c71504) = *(uint *)(iVar3 + -0x73c71504) | 0x20;
            }
            goto LAB_8c01caea;
          }
          iVar3 = *(int *)(_DAT_8c18e48c_maybe_script_some_glb_counter * 4 + -0x73c7150c) * 4;
          uVar2 = *(uint *)(iVar3 + -0x73c71504) | 1;
        }
        else {
          iVar3 = *(int *)(_DAT_8c18e48c_maybe_script_some_glb_counter * 4 + -0x73c7150c) * 4;
          uVar2 = *(uint *)(iVar3 + -0x73c71504) | 2;
        }
        *(uint *)(iVar3 + -0x73c71504) = uVar2;
      }
    }
    else {
      iVar3 = ((*(uint *)(_DAT_8c18e48c_maybe_script_some_glb_counter * 4 + -0x73c7150c) >> 5) + 2)
              * 4;
      *(uint *)(iVar3 + -0x73c7150c) = *(uint *)(iVar3 + -0x73c7150c) | 4;
    }
LAB_8c01caea:
    FUN_8c018fce();
    FUN_8c018fde();
    _DAT_8c18e484_maybe_script_cmd_idx = (_DAT_8c18e484_maybe_script_cmd_idx & 0xffffff00) + 3;
    local_18 = 0;
    local_1c = 0;
    goto LAB_8c01decc_done;
  case 0xd:
    uVar2 = _DAT_8c18e484_maybe_script_cmd_idx & 0xff;
    if (uVar2 == 0) {
      _DAT_8c18e48c_maybe_script_some_glb_counter = _DAT_8c18e48c_maybe_script_some_glb_counter + -8
      ;
      *(undefined4 *)(_DAT_8c18e48c_maybe_script_some_glb_counter * 4 + -0x73c7150c) =
           *(undefined4 *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c);
      iVar3 = _DAT_8c18e488_maybe_script_stack_idx + 2;
      _DAT_8c18e488_maybe_script_stack_idx = _DAT_8c18e488_maybe_script_stack_idx + 1;
      *(undefined4 *)((_DAT_8c18e48c_maybe_script_some_glb_counter + 1) * 4 + -0x73c7150c) =
           *(undefined4 *)(iVar3 * 4 + -0x73c7170c);
      iVar3 = _DAT_8c18e488_maybe_script_stack_idx + 2;
      _DAT_8c18e488_maybe_script_stack_idx = _DAT_8c18e488_maybe_script_stack_idx + 1;
      *(undefined4 *)((_DAT_8c18e48c_maybe_script_some_glb_counter + 2) * 4 + -0x73c7150c) =
           *(undefined4 *)(iVar3 * 4 + -0x73c7170c);
      _DAT_8c18e488_maybe_script_stack_idx = _DAT_8c18e488_maybe_script_stack_idx + 1;
      *(undefined4 *)((_DAT_8c18e48c_maybe_script_some_glb_counter + 4) * 4 + -0x73c7150c) = 0;
      _DAT_8c18e484_maybe_script_cmd_idx = _DAT_8c18e484_maybe_script_cmd_idx & 0xffffff00;
      local_18 = 0;
LAB_8c01d33e:
      _DAT_8c18e484_maybe_script_cmd_idx = _DAT_8c18e484_maybe_script_cmd_idx + 1;
      local_1c = 0;
    }
    else {
      if (uVar2 == 1) {
        FUN_8c018588(1,0);
        FUN_8c01904c(0);
        FUN_8c0199f4(*(undefined4 *)
                      ((_DAT_8c18e48c_maybe_script_some_glb_counter + 1) * 4 + -0x73c7150c));
        FUN_8c019660(0);
        FUN_8c019374();
        if (_DAT_8c0bcf34 == 5) {
          _DAT_8c18e484_maybe_script_cmd_idx = (_DAT_8c18e484_maybe_script_cmd_idx & 0xffffff00) + 2
          ;
        }
        local_18 = 1;
      }
      else {
        if (uVar2 == 2) {
          if (((_DAT_8c0bcf4c & 0x80) != 0) && (_DAT_8c18e4a8 == 1)) {
            FUN_8c0177c0(0x6b);
            if (_DAT_8c18e4a0 == 1) {
              *(undefined4 *)((_DAT_8c18e48c_maybe_script_some_glb_counter + 3) * 4 + -0x73c7150c) =
                   _DAT_8c0bcee8;
              *(undefined4 *)((_DAT_8c18e48c_maybe_script_some_glb_counter + 5) * 4 + -0x73c7150c) =
                   _DAT_8c0bd3ac;
              *(undefined4 *)((_DAT_8c18e48c_maybe_script_some_glb_counter + 6) * 4 + -0x73c7150c) =
                   _DAT_8c0bd448;
              *(undefined4 *)((_DAT_8c18e48c_maybe_script_some_glb_counter + 7) * 4 + -0x73c7150c) =
                   _DAT_8c0bd44c;
              FUN_8c018ad4();
              FUN_8c019b82(0);
              FUN_8c01a4c4(0);
              FUN_8c01a4ca(0);
              *(undefined4 *)(_DAT_8c18e488_maybe_script_stack_idx * 4 + -0x73c7170c) = 0;
              _DAT_8c18e488_maybe_script_stack_idx = _DAT_8c18e488_maybe_script_stack_idx + -1;
              FUN_8c01ea72(&DAT_8c18e484_maybe_script_cmd_idx);
              _DAT_8c18e488_maybe_script_stack_idx = _DAT_8c18e488_maybe_script_stack_idx + 1;
              _DAT_8c18e4a0 = 0;
            }
            else {
              FUN_8c019b82(*(undefined4 *)
                            ((_DAT_8c18e48c_maybe_script_some_glb_counter + 5) * 4 + -0x73c7150c));
              FUN_8c01a4c4(*(undefined4 *)
                            ((_DAT_8c18e48c_maybe_script_some_glb_counter + 6) * 4 + -0x73c7150c));
              FUN_8c01a4ca(*(undefined4 *)
                            ((_DAT_8c18e48c_maybe_script_some_glb_counter + 7) * 4 + -0x73c7150c));
              FUN_8c018a9e();
              FUN_8c018588(1,0);
              *(undefined4 *)(_DAT_8c18e488_maybe_script_stack_idx * 4 + -0x73c7170c) =
                   *(undefined4 *)
                    ((_DAT_8c18e48c_maybe_script_some_glb_counter + 3) * 4 + -0x73c7150c);
              _DAT_8c18e488_maybe_script_stack_idx = _DAT_8c18e488_maybe_script_stack_idx + -1;
              FUN_8c01eba2(&DAT_8c18e484_maybe_script_cmd_idx);
              _DAT_8c18e488_maybe_script_stack_idx = _DAT_8c18e488_maybe_script_stack_idx + 1;
              _DAT_8c18e4a0 = 1;
            }
          }
          if (_DAT_8c18e4a0 == 1) {
            if ((_DAT_8c18e4ac == 1) && ((_DAT_8c0bcf54 & 0x800) != 0)) {
              FUN_8c0177c0(0x65);
              _DAT_8c18e484_maybe_script_cmd_idx =
                   (_DAT_8c18e484_maybe_script_cmd_idx & 0xffffff00) + 4;
            }
            if ((_DAT_8c18e4a0 == 1) &&
               ((((((_DAT_8c0bcf4c & 0x24) != 0 || ((_DAT_8c0bcf4c & 0x41) != 0)) ||
                  ((*(int *)((_DAT_8c18e48c_maybe_script_some_glb_counter + 2) * 4 + -0x73c7150c) <=
                    *(int *)((_DAT_8c18e48c_maybe_script_some_glb_counter + 4) * 4 + -0x73c7150c) &&
                   (0 < *(int *)((_DAT_8c18e48c_maybe_script_some_glb_counter + 2) * 4 + -0x73c7150c
                                ))))) ||
                 ((iVar3 = FUN_8c0173c6(), iVar3 == 1 &&
                  ((*(int *)((_DAT_8c18e48c_maybe_script_some_glb_counter + 2) * 4 + -0x73c7150c) ==
                    -1 || (*(int *)((_DAT_8c18e48c_maybe_script_some_glb_counter + 2) * 4 +
                                   -0x73c7150c) == -2)))))) ||
                ((iVar3 = FUN_8c01315c(1), iVar3 != 0 &&
                 (*(int *)((_DAT_8c18e48c_maybe_script_some_glb_counter + 2) * 4 + -0x73c7150c) ==
                  -2)))))) {
              uVar2 = *(uint *)(_DAT_8c18e48c_maybe_script_some_glb_counter * 4 + -0x73c7150c);
              uVar1 = FUN_8c019a62();
              *(undefined4 *)(((uVar2 >> 5) + 1) * 4 + -0x73c7150c) = uVar1;
              *(undefined4 *)
               (((*(uint *)(_DAT_8c18e48c_maybe_script_some_glb_counter * 4 + -0x73c7150c) >> 5) + 2
                ) * 4 + -0x73c7150c) = 0;
              *(undefined4 *)
               (((*(uint *)(_DAT_8c18e48c_maybe_script_some_glb_counter * 4 + -0x73c7150c) >> 5) + 3
                ) * 4 + -0x73c7150c) =
                   *(undefined4 *)
                    ((_DAT_8c18e48c_maybe_script_some_glb_counter + 4) * 4 + -0x73c7150c);
              if ((*(int *)((_DAT_8c18e48c_maybe_script_some_glb_counter + 4) * 4 + -0x73c7150c) <
                   *(int *)((_DAT_8c18e48c_maybe_script_some_glb_counter + 2) * 4 + -0x73c7150c)) ||
                 (*(int *)((_DAT_8c18e48c_maybe_script_some_glb_counter + 2) * 4 + -0x73c7150c) < 1)
                 ) {
                iVar3 = FUN_8c0173c6();
                if ((iVar3 == 1) &&
                   ((*(int *)((_DAT_8c18e48c_maybe_script_some_glb_counter + 2) * 4 + -0x73c7150c)
                     == -1 || (*(int *)((_DAT_8c18e48c_maybe_script_some_glb_counter + 2) * 4 +
                                       -0x73c7150c) == -2)))) {
                  iVar3 = ((*(uint *)(_DAT_8c18e48c_maybe_script_some_glb_counter * 4 + -0x73c7150c)
                           >> 5) + 2) * 4;
                  *(uint *)(iVar3 + -0x73c7150c) = *(uint *)(iVar3 + -0x73c7150c) | 8;
                }
                else {
                  iVar3 = FUN_8c01315c(0);
                  if ((iVar3 == 0) ||
                     (*(int *)((_DAT_8c18e48c_maybe_script_some_glb_counter + 2) * 4 + -0x73c7150c)
                      != -2)) {
                    if ((_DAT_8c0bcf4c & 0x24) == 0) {
                      FUN_8c0177c0(0x66);
                      iVar3 = ((*(uint *)(_DAT_8c18e48c_maybe_script_some_glb_counter * 4 +
                                         -0x73c7150c) >> 5) + 2) * 4;
                      *(uint *)(iVar3 + -0x73c7150c) = *(uint *)(iVar3 + -0x73c7150c) | 2;
                    }
                    else {
                      FUN_8c0177c0(0x65);
                      iVar3 = ((*(uint *)(_DAT_8c18e48c_maybe_script_some_glb_counter * 4 +
                                         -0x73c7150c) >> 5) + 2) * 4;
                      *(uint *)(iVar3 + -0x73c7150c) = *(uint *)(iVar3 + -0x73c7150c) | 1;
                    }
                  }
                  else if (iVar3 == 1) {
                    iVar3 = ((*(uint *)(_DAT_8c18e48c_maybe_script_some_glb_counter * 4 +
                                       -0x73c7150c) >> 5) + 2) * 4;
                    *(uint *)(iVar3 + -0x73c7150c) = *(uint *)(iVar3 + -0x73c7150c) | 0x10;
                  }
                  else {
                    iVar3 = ((*(uint *)(_DAT_8c18e48c_maybe_script_some_glb_counter * 4 +
                                       -0x73c7150c) >> 5) + 2) * 4;
                    *(uint *)(iVar3 + -0x73c7150c) = *(uint *)(iVar3 + -0x73c7150c) | 0x40;
                  }
                }
              }
              else {
                iVar3 = ((*(uint *)(_DAT_8c18e48c_maybe_script_some_glb_counter * 4 + -0x73c7150c)
                         >> 5) + 2) * 4;
                *(uint *)(iVar3 + -0x73c7150c) = *(uint *)(iVar3 + -0x73c7150c) | 4;
              }
              FUN_8c018fce();
              FUN_8c018fde();
              local_18 = 0;
              _DAT_8c18e484_maybe_script_cmd_idx =
                   (_DAT_8c18e484_maybe_script_cmd_idx & 0xffffff00) + 3;
              local_1c = 0;
              goto LAB_8c01decc_done;
            }
          }
          iVar3 = (_DAT_8c18e48c_maybe_script_some_glb_counter + 4) * 4;
          *(int *)(iVar3 + -0x73c7150c) = *(int *)(iVar3 + -0x73c7150c) + 1;
          FUN_8c01904c(0);
          local_c = 0;
          if ((_DAT_8c0bcf54 & 0x8008) != 0) {
            local_c = -1;
          }
          if ((_DAT_8c0bcf54 & 0x2002) != 0) {
            local_c = local_c + 1;
          }
          bVar5 = (_DAT_8c0bcf54 & 0x1000) != 0;
          if (bVar5) {
            local_c = local_c + -1;
          }
          bVar6 = (_DAT_8c0bcf54 & 0x4000) != 0;
          if (bVar6) {
            local_c = local_c + 1;
          }
          FUN_8c019660(local_c,bVar6 || bVar5);
          FUN_8c019374();
          local_1c = 0;
          local_18 = 1;
          goto LAB_8c01decc_done;
        }
        if (uVar2 == 3) {
          FUN_8c018588(0);
          *(undefined4 *)(_DAT_8c18e488_maybe_script_stack_idx * 4 + -0x73c7170c) = 0xffffffff;
          _DAT_8c18e488_maybe_script_stack_idx = _DAT_8c18e488_maybe_script_stack_idx + -1;
          _DAT_8c18e48c_maybe_script_some_glb_counter =
               _DAT_8c18e48c_maybe_script_some_glb_counter + 8;
          local_1c = 1;
          local_18 = 0;
          _DAT_8c18e498 = (uint)_DAT_8c0bcf54;
          goto LAB_8c01decc_done;
        }
        if (uVar2 != 4) {
          if (uVar2 != 5) {
            FUN_8c010510(s_ipt_exec_coding_error._8c02466c);
            thunk_FUN_8c0104a4(0xffffffff);
            goto LAB_8c01decc_done;
          }
          _DAT_8c18e488_maybe_script_stack_idx = _DAT_8c18e488_maybe_script_stack_idx + 1;
          _DAT_8c18e484_maybe_script_cmd_idx = _DAT_8c18e484_maybe_script_cmd_idx & 0xffffff00;
          local_18 = 1;
          goto LAB_8c01d33e;
        }
        *(uint *)(_DAT_8c18e490_maybe_script_invoke_idx * 4 + -0x73c7190c) =
             (_DAT_8c18e484_maybe_script_cmd_idx & 0xffffff00) + 5;
        _DAT_8c18e490_maybe_script_invoke_idx = _DAT_8c18e490_maybe_script_invoke_idx + -1;
        _DAT_8c18e484_maybe_script_cmd_idx = 0xd27;
        local_18 = 0;
      }
      local_1c = 0;
    }
    goto LAB_8c01decc_done;
  case 0xe:
    uVar2 = _DAT_8c18e484_maybe_script_cmd_idx & 0xff;
    if (uVar2 == 0) {
      FUN_8c01904c(0);
      FUN_8c019986();
      if (_DAT_8c0bcf34 == 5) {
        _DAT_8c18e484_maybe_script_cmd_idx = _DAT_8c18e484_maybe_script_cmd_idx + 1;
      }
    }
    else {
      if (uVar2 != 1) {
        if (uVar2 != 2) {
          FUN_8c010510(s_ipt_exec_coding_error._8c02466c);
          thunk_FUN_8c0104a4(0xffffffff);
          goto LAB_8c01decc_done;
        }
        FUN_8c018fce();
        FUN_8c018fde();
        *(undefined4 *)(_DAT_8c18e488_maybe_script_stack_idx * 4 + -0x73c7170c) = 0xffffffff;
        _DAT_8c18e488_maybe_script_stack_idx = _DAT_8c18e488_maybe_script_stack_idx + -1;
        break;
      }
      FUN_8c01904c(0);
      FUN_8c019986();
      if (_DAT_8c0bcf34 == 5) {
        _DAT_8c18e484_maybe_script_cmd_idx = _DAT_8c18e484_maybe_script_cmd_idx + 1;
      }
    }
    local_1c = 0;
    local_18 = 1;
    goto LAB_8c01decc_done;
  case 0xf:
    local_18 = FUN_8c01ea72(&DAT_8c18e484_maybe_script_cmd_idx);
    goto LAB_8c01d5cc_condi_return;
  case 0x10:
    iVar3 = _DAT_8c18e488_maybe_script_stack_idx + 1;
    uVar1 = FUN_8c016ef6(*(undefined4 *)
                          ((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c));
    *(undefined4 *)(iVar3 * 4 + -0x73c7170c) = uVar1;
    goto LAB_8c01dc08_return;
  case 0x11:
    local_18 = FUN_8c01eab2(&DAT_8c18e484_maybe_script_cmd_idx);
    goto LAB_8c01d5cc_condi_return;
  case 0x12:
    local_18 = FUN_8c01eaee(&DAT_8c18e484_maybe_script_cmd_idx);
    goto LAB_8c01d5cc_condi_return;
  case 0x13:
    local_18 = FUN_8c01eb2a(&DAT_8c18e484_maybe_script_cmd_idx);
    goto LAB_8c01d5cc_condi_return;
  case 0x14:
    local_18 = FUN_8c01eb66(&DAT_8c18e484_maybe_script_cmd_idx);
    goto LAB_8c01d5cc_condi_return;
  case 0x15:
    local_18 = FUN_8c01eba2(&DAT_8c18e484_maybe_script_cmd_idx);
    goto LAB_8c01d5cc_condi_return;
  case 0x16:
    FUN_8c019b82(*(undefined4 *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c));
    *(undefined4 *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c) = 0xffffffff;
    break;
  case 0x17:
    FUN_8c019b88(*(undefined4 *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c));
    *(undefined4 *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c) = 0xffffffff;
    break;
  case 0x18:
    FUN_8c019bc0(*(undefined4 *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c),
                 *(undefined4 *)((_DAT_8c18e488_maybe_script_stack_idx + 2) * 4 + -0x73c7170c));
    iVar3 = _DAT_8c18e488_maybe_script_stack_idx + 2;
    _DAT_8c18e488_maybe_script_stack_idx = _DAT_8c18e488_maybe_script_stack_idx + 1;
    *(undefined4 *)(iVar3 * 4 + -0x73c7170c) = 0xffffffff;
    goto LAB_8c01dc08_return;
  case 0x19:
    FUN_8c01a4c4(*(undefined4 *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c));
    *(undefined4 *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c) = 0xffffffff;
    break;
  case 0x1a:
    FUN_8c01a4d0(_DAT_8c38eca8,_DAT_8c38eca4,_DAT_8c38ecb0);
    iVar3 = _DAT_8c18e488_maybe_script_stack_idx * 4;
    _DAT_8c18e488_maybe_script_stack_idx = _DAT_8c18e488_maybe_script_stack_idx + -1;
    *(undefined4 *)(iVar3 + -0x73c7170c) = 0xffffffff;
    goto LAB_8c01dc08_return;
  case 0x1b:
    FUN_8c01a4ca(*(undefined4 *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c));
    *(undefined4 *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c) = 0xffffffff;
    break;
  case 0x1c:
    local_18 = FUN_8c01ebe6(&DAT_8c18e484_maybe_script_cmd_idx);
LAB_8c01d5cc_condi_return:
    local_1c = _DAT_8c18e494_syscall_subc_ret;
    goto LAB_8c01decc_done;
  case 0x1d:
    FUN_8c0175c6(*(undefined4 *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c),
                 *(undefined4 *)((_DAT_8c18e488_maybe_script_stack_idx + 2) * 4 + -0x73c7170c),
                 *(undefined4 *)((_DAT_8c18e488_maybe_script_stack_idx + 3) * 4 + -0x73c7170c),
                 *(undefined4 *)((_DAT_8c18e488_maybe_script_stack_idx + 4) * 4 + -0x73c7170c));
    iVar3 = _DAT_8c18e488_maybe_script_stack_idx + 4;
    _DAT_8c18e488_maybe_script_stack_idx = _DAT_8c18e488_maybe_script_stack_idx + 3;
    *(undefined4 *)(iVar3 * 4 + -0x73c7170c) = 0xffffffff;
    goto LAB_8c01dc08_return;
  case 0x1e:
    thunk_FUN_8c0139e2(*(undefined4 *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c)
                      );
    *(undefined4 *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c) = 0xffffffff;
    break;
  case 0x1f:
    FUN_8c0177c0(*(undefined4 *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c));
    *(undefined4 *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c) = 0xffffffff;
    break;
  case 0x20:
    iVar4 = _DAT_8c18e488_maybe_script_stack_idx * 4;
    _DAT_8c18e488_maybe_script_stack_idx = _DAT_8c18e488_maybe_script_stack_idx + -1;
    iVar3 = FUN_8c013aa4();
    *(uint *)(iVar4 + -0x73c7170c) = (uint)(iVar3 != 0);
    goto LAB_8c01dc08_return;
  case 0x21:
    if ((_DAT_8c18e484_maybe_script_cmd_idx & 0xff) == 0) {
      uVar1 = *(undefined4 *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c);
      _DAT_8c18e488_maybe_script_stack_idx = _DAT_8c18e488_maybe_script_stack_idx + 1;
      FUN_8c01e044();
      *(uint *)(_DAT_8c18e490_maybe_script_invoke_idx * 4 + -0x73c7190c) =
           (_DAT_8c18e484_maybe_script_cmd_idx & 0xffffff00) + 1;
      _DAT_8c18e490_maybe_script_invoke_idx = _DAT_8c18e490_maybe_script_invoke_idx + -1;
      iVar3 = _DAT_8c18e488_maybe_script_stack_idx * 4;
      _DAT_8c18e488_maybe_script_stack_idx = _DAT_8c18e488_maybe_script_stack_idx + -1;
      *(undefined4 *)(iVar3 + -0x73c7170c) = uVar1;
      _DAT_8c18e484_maybe_script_cmd_idx = 0x1f9b;
      local_18 = 0;
      local_1c = 0;
      goto LAB_8c01decc_done;
    }
    if ((_DAT_8c18e484_maybe_script_cmd_idx & 0xff) != 1) {
      FUN_8c010510(s_ipt_exec_coding_error._8c02466c);
      thunk_FUN_8c0104a4(0xffffffff);
      goto LAB_8c01decc_done;
    }
    _DAT_8c18e488_maybe_script_stack_idx = _DAT_8c18e488_maybe_script_stack_idx + 1;
    FUN_8c01e5e4();
    iVar3 = _DAT_8c18e488_maybe_script_stack_idx * 4;
    _DAT_8c18e488_maybe_script_stack_idx = _DAT_8c18e488_maybe_script_stack_idx + -1;
    *(undefined4 *)(iVar3 + -0x73c7170c) = 0xffffffff;
    goto LAB_8c01dc08_return;
  case 0x22:
    uVar1 = FUN_8c017344();
    FUN_8c01734a(*(undefined4 *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c),
                 s_BISLPS-02360_8c024684,uVar1,0);
    FUN_8c0172dc(&DAT_8c03f7c6 +
                 *(int *)((_DAT_8c18e488_maybe_script_stack_idx + 2) * 4 + -0x73c7170c) * 0x40,
                 &DAT_8c03f806 +
                 *(int *)((_DAT_8c18e488_maybe_script_stack_idx + 2) * 4 + -0x73c7170c) * 0x20,
                 &DAT_8c03f826 +
                 *(int *)((_DAT_8c18e488_maybe_script_stack_idx + 2) * 4 + -0x73c7170c) * 0x80);
    iVar3 = _DAT_8c18e488_maybe_script_stack_idx + 2;
    _DAT_8c18e488_maybe_script_stack_idx = _DAT_8c18e488_maybe_script_stack_idx + 1;
    *(undefined4 *)(iVar3 * 4 + -0x73c7170c) = 0xffffffff;
    break;
  case 0x23:
    iVar3 = _DAT_8c18e488_maybe_script_stack_idx * 4;
    _DAT_8c18e488_maybe_script_stack_idx = _DAT_8c18e488_maybe_script_stack_idx + -1;
    uVar1 = FUN_8c0173b8();
    *(undefined4 *)(iVar3 + -0x73c7170c) = uVar1;
    goto LAB_8c01dc08_return;
  case 0x24:
    FUN_8c0173b2(*(undefined4 *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c));
    *(undefined4 *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c) = 0xffffffff;
    break;
  case 0x25:
    iVar3 = *(int *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c);
    if (iVar3 != 0) {
      if (iVar3 == 1) {
        if ((_DAT_8c38eca8 == 0) || (_DAT_8c38eca8 == 1)) {
          FUN_8c012f22(_DAT_8c38ecb0,_DAT_8c38eca4,_DAT_8c38fb1c);
        }
        else {
          FUN_8c012f22(_DAT_8c38ecb0,0xffffffff,_DAT_8c38fb1c);
        }
        FUN_8c01f230();
        FUN_8c012486(0x8c38faf4);
      }
      else if (iVar3 == 2) {
        FUN_8c0124b8(0x8c38faf4);
      }
    }
    *(undefined4 *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c) = 0xffffffff;
    break;
  case 0x26:
    uVar1 = FUN_8c012ef0(*(undefined4 *)
                          ((_DAT_8c18e488_maybe_script_stack_idx + 2) * 4 + -0x73c7170c),
                         *(undefined4 *)
                          ((_DAT_8c18e488_maybe_script_stack_idx + 3) * 4 + -0x73c7170c));
    *(undefined4 *)
     (((*(uint *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c) >> 5) + 4) * 4 +
     -0x73c7150c) = _DAT_8c0b76b0;
    *(undefined4 *)
     (((*(uint *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c) >> 5) + 5) * 4 +
     -0x73c7150c) = _DAT_8c0b76b4;
    *(undefined4 *)
     (((*(uint *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c) >> 5) + 6) * 4 +
     -0x73c7150c) = _DAT_8c0b76b8;
    iVar3 = _DAT_8c18e488_maybe_script_stack_idx + 3;
    _DAT_8c18e488_maybe_script_stack_idx = _DAT_8c18e488_maybe_script_stack_idx + 2;
    *(undefined4 *)(iVar3 * 4 + -0x73c7170c) = uVar1;
    goto LAB_8c01dc08_return;
  case 0x27:
    iVar3 = _DAT_8c18e488_maybe_script_stack_idx + 1;
    uVar1 = FUN_8c013144(*(undefined4 *)
                          ((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c));
    *(undefined4 *)(iVar3 * 4 + -0x73c7170c) = uVar1;
    goto LAB_8c01dc08_return;
  case 0x28:
    FUN_8c0130f2(*(undefined4 *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c));
    *(undefined4 *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c) = 0xffffffff;
    break;
  case 0x29:
    iVar3 = _DAT_8c18e488_maybe_script_stack_idx * 4;
    _DAT_8c18e488_maybe_script_stack_idx = _DAT_8c18e488_maybe_script_stack_idx + -1;
    uVar1 = FUN_8c01693a();
    *(undefined4 *)(iVar3 + -0x73c7170c) = uVar1;
    goto LAB_8c01dc08_return;
  case 0x2a:
    FUN_8c01692a(*(undefined4 *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c));
    *(undefined4 *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c) = 0xffffffff;
    break;
  case 0x2b:
    FUN_8c01df50();
    iVar3 = _DAT_8c18e488_maybe_script_stack_idx * 4;
    _DAT_8c18e488_maybe_script_stack_idx = _DAT_8c18e488_maybe_script_stack_idx + -1;
    *(undefined4 *)(iVar3 + -0x73c7170c) = 0xffffffff;
    goto LAB_8c01dc08_return;
  case 0x2c:
    FUN_8c01def2();
    iVar3 = _DAT_8c18e488_maybe_script_stack_idx * 4;
    _DAT_8c18e488_maybe_script_stack_idx = _DAT_8c18e488_maybe_script_stack_idx + -1;
    *(undefined4 *)(iVar3 + -0x73c7170c) = 0xffffffff;
    break;
  case 0x2d:
    FUN_8c01e212();
    iVar3 = _DAT_8c18e488_maybe_script_stack_idx * 4;
    _DAT_8c18e488_maybe_script_stack_idx = _DAT_8c18e488_maybe_script_stack_idx + -1;
    *(undefined4 *)(iVar3 + -0x73c7170c) = 0xffffffff;
    goto LAB_8c01dc08_return;
  case 0x2e:
    FUN_8c01e104();
    iVar3 = _DAT_8c18e488_maybe_script_stack_idx * 4;
    _DAT_8c18e488_maybe_script_stack_idx = _DAT_8c18e488_maybe_script_stack_idx + -1;
    *(undefined4 *)(iVar3 + -0x73c7170c) = 0xffffffff;
    break;
  case 0x2f:
    FUN_8c01e7cc();
    iVar3 = _DAT_8c18e488_maybe_script_stack_idx * 4;
    _DAT_8c18e488_maybe_script_stack_idx = _DAT_8c18e488_maybe_script_stack_idx + -1;
    *(undefined4 *)(iVar3 + -0x73c7170c) = 0xffffffff;
    goto LAB_8c01dc08_return;
  case 0x30:
    FUN_8c017032();
    iVar3 = _DAT_8c18e488_maybe_script_stack_idx * 4;
    _DAT_8c18e488_maybe_script_stack_idx = _DAT_8c18e488_maybe_script_stack_idx + -1;
    *(undefined4 *)(iVar3 + -0x73c7170c) = 0xffffffff;
    break;
  case 0x31:
    iVar3 = _DAT_8c18e488_maybe_script_stack_idx + 1;
    uVar1 = FUN_8c01704e(*(undefined4 *)
                          ((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c));
    *(undefined4 *)(iVar3 * 4 + -0x73c7170c) = uVar1;
    goto LAB_8c01dc08_return;
  case 0x32:
    FUN_8c0170a8(*(undefined4 *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c),
                 *(undefined4 *)((_DAT_8c18e488_maybe_script_stack_idx + 2) * 4 + -0x73c7170c));
    iVar3 = _DAT_8c18e488_maybe_script_stack_idx + 2;
    _DAT_8c18e488_maybe_script_stack_idx = _DAT_8c18e488_maybe_script_stack_idx + 1;
    *(undefined4 *)(iVar3 * 4 + -0x73c7170c) = 0xffffffff;
LAB_8c01dc08_return:
    local_1c = 1;
    local_18 = 0;
    goto LAB_8c01decc_done;
  case 0x33:
    if (_DAT_8c09ebf4 != 0) {
      _DAT_8c09ebf4 = 0;
      _DAT_8c18e484_maybe_script_cmd_idx = (_DAT_8c18e484_maybe_script_cmd_idx & 0xffffff00) + 3;
    }
    uVar2 = _DAT_8c18e484_maybe_script_cmd_idx & 0xff;
    if (uVar2 == 0) {
      iVar3 = FUN_8c018050();
      if (((iVar3 == 0) || (iVar3 = FUN_8c019ace(), iVar3 == 1)) ||
         ((iVar3 = FUN_8c016cf8(0xffffffff), iVar3 == 1 || (iVar3 = FUN_8c018f36(), iVar3 == 1)))) {
        _DAT_8c18e484_maybe_script_cmd_idx = (_DAT_8c18e484_maybe_script_cmd_idx & 0xffffff00) + 1;
        FUN_8c013ab8();
      }
LAB_8c01dcfe_no_return:
      local_1c = 0;
      local_18 = 1;
      goto LAB_8c01decc_done;
    }
    if (uVar2 == 1) {
      iVar3 = FUN_8c010f32();
      if (iVar3 != 0) {
        FUN_8c01ece4(2);
        _DAT_8c18e484_maybe_script_cmd_idx = (_DAT_8c18e484_maybe_script_cmd_idx & 0xffffff00) + 2;
        local_1c = 0;
        local_18 = 1;
      }
      goto LAB_8c01decc_done;
    }
    if (uVar2 == 2) {
      iVar3 = FUN_8c01123e();
      if ((iVar3 == 0) || ((_DAT_8c0bcf4c & 0xeff) != 0)) {
        FUN_8c011696();
        _DAT_8c18e484_maybe_script_cmd_idx = (_DAT_8c18e484_maybe_script_cmd_idx & 0xffffff00) + 3;
      }
      goto LAB_8c01dcfe_no_return;
    }
    if (uVar2 != 3) {
      FUN_8c010510(s_ipt_exec_coding_error._8c02466c);
      thunk_FUN_8c0104a4(0xffffffff);
      goto LAB_8c01decc_done;
    }
    FUN_8c01ece4(1);
    *(undefined4 *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c) = 0xffffffff;
    local_18 = 1;
    goto LAB_8c01de7c_return;
  case 0x34:
    uVar2 = _DAT_8c18e484_maybe_script_cmd_idx & 0xff;
    if (uVar2 == 0) {
      iVar3 = FUN_8c018050();
      if ((((iVar3 == 0) || (iVar3 = FUN_8c019ace(), iVar3 == 1)) ||
          (iVar3 = FUN_8c016cf8(0xffffffff), iVar3 == 1)) || (iVar3 = FUN_8c018f36(), iVar3 == 1)) {
        _DAT_8c18e484_maybe_script_cmd_idx = (_DAT_8c18e484_maybe_script_cmd_idx & 0xffffff00) + 1;
      }
    }
    else if (uVar2 == 1) {
      FUN_8c01ece4(3);
      FUN_8c01afe8(*(undefined4 *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c));
      _DAT_8c18e484_maybe_script_cmd_idx = (_DAT_8c18e484_maybe_script_cmd_idx & 0xffffff00) + 2;
    }
    else {
      if (uVar2 != 2) {
        if (uVar2 != 3) {
          FUN_8c010510(s_ipt_exec_coding_error._8c02466c);
          thunk_FUN_8c0104a4(0xffffffff);
          goto LAB_8c01decc_done;
        }
        FUN_8c01b4e4();
        FUN_8c01ece4(1);
        *(undefined4 *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c) = 0xffffffff;
        local_18 = 1;
        goto LAB_8c01de7c_return;
      }
      iVar3 = FUN_8c01b4ce();
      if ((iVar3 == 1) || ((_DAT_8c0bcf4c & 0xeff) != 0)) {
        _DAT_8c18e484_maybe_script_cmd_idx = (_DAT_8c18e484_maybe_script_cmd_idx & 0xffffff00) + 3;
      }
    }
    local_1c = 0;
    local_18 = 1;
    goto LAB_8c01decc_done;
  case 0x35:
    FUN_8c0104da(*(undefined4 *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c));
    local_1c = 1;
    local_18 = 0;
    goto LAB_8c01decc_done;
  case 0x36:
    FUN_8c0159b6(*(undefined4 *)((_DAT_8c18e488_maybe_script_stack_idx + 1) * 4 + -0x73c7170c));
    local_18 = 0;
    local_1c = 1;
    goto LAB_8c01decc_done;
  default:
    local_18 = 1;
    local_1c = 0;
    goto LAB_8c01decc_done;
  }
  local_18 = 0;
LAB_8c01de7c_return:
  local_1c = 1;
LAB_8c01decc_done:
  if (local_1c == 1) {
    _DAT_8c18e484_maybe_script_cmd_idx =
         *(uint *)((_DAT_8c18e490_maybe_script_invoke_idx + 1) * 4 + -0x73c7190c);
    _DAT_8c18e490_maybe_script_invoke_idx = _DAT_8c18e490_maybe_script_invoke_idx + 1;
  }
  return local_18;
}

