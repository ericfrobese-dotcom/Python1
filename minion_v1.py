def minion_game(string):
    vls = "AEIOU"
    # Stuart scores for strings starting w/ consonants and Kevin has Vowels
    score = {}
    for p in range (0, len(string), 1):
        c = string[p]
        if c not in score:
            score[c] = string.count(c)
    #print('vls = {}  score:\n{}'.format(vls,score))
    #tally score
    ss = 0
    ks = 0
    for l in score:
        if vls.find(l) < 0:
            ss += score[l]
        else:
            ks += score[l]
    print('Single letter scores Vowels (Kevin): {} Const (Stuart): {}'.format(ks,ss))
    # Starting Char Position
    for scp in range (0, len(string)-1):
        # Word Length
        for wl in range(scp+2, len(string)+1):
            w = string[scp:wl]
            # Sub Total
            st = 0
            #print('scp = {}  wl = {}  w = {}'.format(scp, wl, w))
            if w not in score:
                if vls.find(w[0]) < 0:
                    ss += 1
                    st += 1
                    #print('ss increased to: {}'.format(ss))
                else:
                    ks += 1
                    st += 1
                    #print('ks increased to: {}'.format(ks))
                ts = string[scp+1:]
                p = ts.find(w)
                while p > -1:
                    if vls.find(w[0]) < 0:
                        ss += 1
                        #print('ss incremented to {} for {} at {}'.format(ss,w,p))
                        st += 1
                    else:
                        ks += 1
                        #print('ks incremented to {} for {} at {}'.format(ks,w,p))
                        st += 1
                    ts = ts[(p+1):]
                    p = ts.find(w)
                score[w] = st
    #print('ks = {}  ss = {}   score:\n{}'.format(ks,ss,score))
    if ks > ss:
        print('{} {}'.format("Kevin",ks))
    elif ss > ks:
        print('{} {}'.format('Stuart',ss))
    else:
        print('Draw')
            
if __name__ == '__main__':