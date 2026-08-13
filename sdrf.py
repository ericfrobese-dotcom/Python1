# Scan Directory Rename Files
import os
import re
import time

# file scan and rename
hd = os.getcwd() # Home Directory
td = 'C:\\files from linux'
rexp = r'^[\d]{13}\.txt$'  # regular expression to match mirth generated files
tfmo = re.compile(rexp)  # Target File Match Object
os.chdir(td)
scan = True
print('Scanning {}...'.format(td))
while scan:
    ls = os.listdir()
    for f in ls:
        if tfmo.match(f):
            print('Found file {}, waiting to ensure completion...'.format(f))
            #time.sleep(5)
            fo = open(f,'rb')
            msg = fo.read()  # message
            fo.close()
            av = msg.decode() # ascii version
            rp = av.find(chr(13))  # retrun character position
            np = av.find(chr(10))  # Newline character position
            ps = av[0] == chr(11)  # Pad Start
            sp = 1 if ps else 0
            ep = len(av)  # End Position
            if np < 0 or (rp > -1 and rp < np):
                ep = rp
            elif rp < 0 or (np < rp):
                ep = np
            print('rp = {}  np = {}  sp = {} ep = {}'.format(rp,np,sp,ep))
            fl = av[sp:ep] 
            if fl.find('/') == fl.find('\\'):  #means no file name passed
                fl = '//' + ls[0]
            dsc = '/' if fl.find('/')>-1 else '\\'
            print('first line:\n{}'.format(fl)) 
            while fl[0] == chr(11):
                fl = fl[1:]
            chop = fl.find(dsc)
            while chop != -1:
                fl = fl[chop+1:]
                chop = fl.find(dsc)
            nfn = fl  # New File Name
            print('nfn = {}'.format(nfn))
            lc = chr(11) if ps else ''  # Lead Character
            av = lc + av[ep+1:]
            msg = av.encode()
            sd = bytearray(msg)  # Send Data
            if nfn in ls:
                print('{} already exists'.format(nfn))
                nfn = 'p' + f
            print('New File name = {}'.format(nfn))
            time.sleep(2)
            fo = open(nfn,'wb')
            fo.write(sd)
            fo.close()
            print('Deleting file name {}'.format(f))
            os.remove(f)
            a = input('Continue Scanning? ')
            if a[0].lower() == 'n':
                scan = False
                break
            print('Current scan value = {}'.format(scan))
    if not scan:
        break
    time.sleep(30)