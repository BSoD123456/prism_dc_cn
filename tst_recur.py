'''
func r1():
    jump_if(push(1), push(la))
    pop(call(push(1), r2))
    return(push(3))

func r2(a1):
    jump_if(push(1), push(la))
    return(call(a1, r2))
    jump_if(a1, push(lb))
    return(call(r1))
    return(call(push(3), r2))

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
a push f
b jump if

c push 9
d call
d return

f push 14
10 jump if

11 push 0
12 call
13 return

14 push 3
15 push 9
16 call
17 return
'''

with open('wktab/tst_recur1.bin', 'wb') as fd:
    fd.write(bytes.fromhex('''
        01000028 07000028 15000040
        01000028 09000028 00000048 00000030
        03000028 00000058
        
        01000028 0f000028 15000040
        09000028 00000048
        00000058
        14000028 15000040
        00000028 00000048
        00000058
        03000028 09000028 00000048
        00000058
    '''))

'''
pop(push(1))
jump force 0
'''

with open('wktab/tst_noret.bin', 'wb') as fd:
    fd.write(bytes.fromhex('''
        01000028 00000030
        00000028 14000040
    '''))
