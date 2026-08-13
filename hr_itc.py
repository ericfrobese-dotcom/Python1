#winner:
# Enter your code here. Read input from STDIN. Print output to STDOUT
from itertools import permutations
import sys

z = sys.stdin
for l in z:
    ll = l.split()
    #print('l = {}  ll = {}'.format(l,ll))
    s = ll[0]
    k = int(ll[1])
print(*[''.join(i) for i in permutations(sorted(s),k)],sep='\n')#permutations(s,k)


#>> first version:
# Enter your code here. Read input from STDIN. Print output to STDOUT
from itertools import permutations
import sys

#z = sys.stdin
#for l in z:
#    ll = l.split()
#    #print('l = {}  ll = {}'.format(l,ll))
#    s = ll[0]
#    k = int(ll[1])
s = input('Enter S string: ')
k = int(input('Enter integer k: '))
s = sorted(s)
ls = []
ls = permutations(s,k)
#ls = sorted(ls)
for t in ls:
    print('{}{}'.format(t[0],t[1]))