import re
def fdp(n,dp):
    sn = str(round(n,dp))
    p = sn.find('.')
    if p < 0:
        return sn + '.' + ('0' * dp)
    else:
        z = sn[(p+1):]
        while len(z) < 2:
            z += '0'
        return(sn[:(p+1)] + z)

#f = float(input('Enter float number: '))
#d = int(input('Enter decimal places desired: '))

#r = fdp(f, d)
#print('The new fdp function returns: {}'.format(r))
inst = {"@instagram":69,
        "@selenagomez":133,
        "@victoriassecret": 59,
        "@cristiano":120,
        "@beyonce":111,
        "@nike":76}

twit = {"@cristiano":69,
        "@barackobama":100,
        "@ladygaga":70,
        "@selenagomez":56,
        "@realdonaldtrump":48}

inst_names = set(filter(lambda x: inst[x]>60,inst.keys()))
twit_names = set(filter(lambda x: twit[x]>60,twit.keys()))

ss = inst_names.intersection(twit_names)
print(list(ss)[0])
print('ss = {}  len(ss) = {}'.format(ss,len(ss)))