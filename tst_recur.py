'''
func r1():
    jump_if(push(1), push(la))
    pop(call(push(1), r2))
    return(push(3))

func r2(a1):
    jump_if(push(1), push(la))
    return(call(push(2), r2))
    jump_if(push(1), push(lb))
    return(call(r1))
    jump_if(push(1), push(lc))
    return(a1)
    return(call(a1, r2))

0 push 1
1 push 7
2 jump if
3 push 1
4 push 9
5 call
6 pop
7 push 3
8 return

9 push 1
a push 10
b jump if
c push 2
d push 9
e call
f return
10 push 1
11 push 16
12 jump if
13 push 0
14 call
15 return
16 push 1
17 push 1a
18 jump if
19 return
1a push 9
1b call
1c return
'''

with open('wktab/tst_recur.bin', 'wb') as fd:
    fd.write(bytes.fromhex('''
        01000028 07000028 15000040
        01000028 09000028 00000048 00000030
        03000028 00000058
        
        01000028 10000028 15000040
        02000028 09000028 00000048
        00000058
        01000028 16000028 15000040
        00000028 00000048
        00000058
        01000028 1a000028 15000040
        00000058
        09000028 00000048
        00000058
    '''))
