# GUI File Utility Project- plan to create Windows and Linux executables of this code 
from tkinter import *
from tkinter import filedialog
from tkinter import messagebox as mb
import os
import shutil
import getpass
import datetime as dt
import webbrowser
#setRunDir = True
setRunDir = False
home = os.getcwd()
if setRunDir:
    if home.find('/') > -1:
        #running on my Linux machine
        os.chdir('/home/eric/Documents')
    else:
        # Windows 10 Lenovo ThinkPad
        os.chdir('C:\\Users\\Owner\\Documents\\Python3 source code')
        home = os.getcwd()
print('home dir = {}'.format(home))
class win(Frame):
    def __init__(self, master = None):
        Frame.__init__(self,master)
        self.master = master
        self.init_window()
        
    def init_window(self):
        self.master.title("File Propagate -by EJF")
        self.grid(row = 0)
        menu = Menu(self.master)
        self.master.config(menu=menu)
        # File Menu
        file = Menu(menu)
        file.add_command(label='Load Profile', command = self.loadProfile)
        file.add_command(label='Save Profile', command = self.saveProfile)
        file.add_command(label='Exit', command = self.client_exit)
        menu.add_cascade(label='File', menu=file)
        # Tools Menu
        tools = Menu(menu)
        tools.add_command(label='Start Prop',command=self.startProp)
        menu.add_cascade(label='Tools', menu=tools)
        # Document Menu
        documentation = Menu(menu)
        documentation.add_command(label = 'View Documentation',command=self.viewDoc)
        menu.add_cascade(label = 'Documentation', menu = documentation)
        # Class Shared Variables
        self.sf = ''  # Source File
        self.dd = ''  # destination dictionary
        self.df = 'File Propagate Documentation.pdf'  # Documentaion File
        self.runDir = os.getcwd()  # Run Dir
        self.dsc = '/' if self.runDir.find('\\') < 0 else '\\'
        # need to tie down a save dir in DEBIAN launched app, check for DEBIAN Package
        debian = False
        if self.dsc == '/':
            user = getpass.getuser()
            td = '/etc'
            os.chdir(td)
            ls = os.listdir()
            debian = 'apt' in ls
            if debian:
                dn = '/home/'+user+'/Documents'
                os.chdir(dn)
                ls = os.listdir()
                if 'fpd' not in ls:
                    os.mkdir('fpd')
                    try:
                        shutil.move(self.runDir +self.dsc + self.df, dn + '/fpd')
                    except:
                        e = sys.exc_info()
                        print('Could not install Documentation file, Error:\n{}'.format(e))
                self.fpdPath = dn +'/fpd'
                # Check Documentation file
                ls = os.listdir(self.fpdPath)
                if self.df not in ls:
                    try:
                        shutil.move(self.runDir + self.dsc + self.df, self.fpdPath)
                    except:
                        e = sys.exc_info()
                        print('Could not install Documentation file, Error:\n{}'.format(e))
        else:
            self.fpdPath = self.runDir + self.dsc + 'fpd'  # file Propagage Data Path
        print('debian = {}  self.fpdPath = {}'.format(debian,self.fpdPath))
        # Maybe create data save directory
        ls = os.listdir()
        if 'fpd' not in ls:
            os.mkdir('fpd')  #File Propagate Data
            try:
                shutil.move(self.runDir + self.dsc + self.df , self.fpdPath)
            except:
                        e = sys.exc_info()
                        print('Could not install Documentation file, Error:\n{}'.format(e))
        # Rows 1 and 2 Profile Management
        self.loadProfileButton = Button(self, text = 'Load Profile', command = self.loadProfile)
        self.loadProfileButton.grid(row = 1, column = 1, sticky = W)
        self.labelProfile = Label(self, text = 'Profile')
        self.labelProfile.grid(row=1, pady = 4, padx = 4, sticky = W)
        self.profileEntry = Entry(self, width = 80)
        self.profileEntry.grid(row = 2, pady = 4, padx = 4, sticky = W)
        self.SaveProfileButton = Button(self, text = 'Save Profile', command = self.saveProfile)
        self.SaveProfileButton.grid(row = 2, column = 1, sticky = W)
        # Row 3 Blank
        # Row 4 <<Status line>>
        self.status = StringVar()
        self.status_label = Label(self,bg='black',fg='white', textvariable = self.status)
        self.status.set(' -- General Status Info --')
        self.status_label.grid(row = 4, padx = 4)
        # Row 5 - Source File List 
        self.sfButton = Button(self, text = 'Add Source File', command = self.chooseFile)
        self.sfButton.grid(row = 5, column = 1, sticky = W)
        self.twsf = Text(self, height = 3, width = 80)  # Text Widget Source Files
        self.twsf.grid(row = 5, padx = 4, sticky = W)        
        # Row 7 - Destination Directory List
        self.ddButton = Button(self, text = 'Add Destination Dir', command = self.selectDir)
        self.ddButton.grid(row = 7, column = 1, sticky = W)
        self.twdd = Text(self, height = 6, width = 80)  # Text Widget Inbound Message
        self.twdd.grid(row = 7, padx = 4, sticky = W)
        # Row 8 - Start Propagate Button
        self.spButton = Button(self, text = "Start Propagation", command = self.startProp)
        self.spButton.grid(row = 8)

    def gStat(self, msg, f = 'white', b = 'black'):
        self.status.set(msg)
        self.status_label.config(bg = b, fg = f)
        self.status_label.grid(row = 4, padx = 4)
        
    def viewDoc(self):
        fn = self.df  # Documentation file
        #c = os.getcwd()
        # may need to move documentation file to data dir
        ls = os.listdir(self.fpdPath)
        found = fn in ls
        if not found:
            ls = os.listdir(self.runDir)
            if fn in ls:
                shutil.move(self.runDir + self.dsc + self.df, self.fpdPath)
            else:
                mb.showerror('Documentation file Missing',"Can not find document file, sorry.")
                self.gStat('Documentation file "{}" not found in data directory.'.format(fn),'black','red')
                return
        if self.dsc == '/':  # Use webbrowser to display pdf in linux
            fp = self.fpdPath + '/' + fn  # Full Path doc file
            webbrowser.open(r'file:{}'.format(fp))
        else:                # Os startfile works great to display pdf in windows 10
            c = os.getcwd()
            os.chdir(self.fpdPath)
            os.startfile(fn)
            os.chdir(c)
        self.gStat('Documenation launched.')
        
    def saveProfile(self):
        pn = self.profileEntry.get()
        ok =  True
        if len(pn) == 0:
            mb.showerror('No Profile Name', 'Enter a name in box below "Profile" label')
            ok = False
        if ok:
            self.gStat('Saving Profile: {}'.format(pn))
            hasExt = re.match(r'\w+\.fpp$',pn)
            if not hasExt: pn = pn + '.fpp'
            pfn = self.fpdPath + self.dsc + pn  #full Profile File Name 
            # Handle Text Widgets up front will save to different ext off base profile name
            bfn = pfn[:-4]
            print('saving profile = {}'.format(bfn))
            twddv = self.twdd.get("1.0",'end-1c')
            if len(twddv) > 0:
                ddfn = bfn + '.fdd' # Destination Dir File Name
                fo = open(ddfn,'wt')
                fo.write(twddv)
                fo.close()
            twsfv =  self.twsf.get(1.0,'end-1c')
            if len(twsfv) > 0:
                sffn = bfn + '.fsf' # Source File File Name
                fo = open(sffn,'wt')
                fo.write(twsfv)
                fo.close()
            sd = ''
            sd = sd + 'END\n'
        fo = open(pfn,'wt')
        fo.write(sd)
        fo.close()
        print('Profile {} Saved.'.format(pn))
        self.gStat('Profile {} Saved.'.format(pn))

    def client_exit(self):
        root.destroy()
    
    def selectDir(self):
        cwd = os.getcwd()
        dd = filedialog.askdirectory(parent = self, initialdir = cwd, title = 'Select Directory')
        self.twdd.insert(END, dd+'\n')
        self.twdd.grid(row = 7, padx = 4, sticky = W)
        m = 'Directory {} added to Destination Directories'.format(dd)
        print(m)
        self.gStat(m)
    
    def loadProfile(self):
        # Load Values Section
        # load in any save data (starting off just using a file)        
        pn = filedialog.askopenfilename(initialdir = self.fpdPath, title = 'Select Profile', filetypes = (("Profiles","*.fpp"),("all files","*.*")))
        twd = ''  # Text Widget Data
        ldscp = len(pn)  # Last Directory Separator Character Position
        #might not have selected a file..
        if ldscp > 0:
            ldscp -= 1
            while pn[ldscp] != '/':
                ldscp -= 1
            self.fpdPath = pn[:ldscp]
        fo = open(pn,'rt')
        sd = fo.read()  # Source Data 
        fo.close()
        bf = pn[:-4]
        # bf includes full path, need to remove path for value to check in direcotry..
        jfb = bf  # Just File Base w/out path (or extention)
        chop = jfb.find('/')
        while chop != -1:
            jfb = jfb[chop+1:]
            chop = jfb.find('/')
        print('Loading profile {}'.format(bf))
        os.chdir(self.fpdPath)
        ls = os.listdir()  # Array with current directoery (like the linux BASH command)
        #omfn = bf + '.tom'  since we are now in fdp dir don't need full path
        ddf = jfb + '.fdd'
        #print('jf = {}  in ls = {}'.format(jf, jf in ls))
        if ddf in ls:
            fo = open(ddf,'rt')
            twd = fo.read()
            fo.close()
        self.twdd.delete(1.0, END)
        self.twdd.insert(1.0, twd)
        self.twdd.grid(row = 7, padx = 4, sticky = W)
        # re-using twd for all text widget fields on screen
        twd = ''
        sfn = jfb + '.fsf'
        if sfn in ls:
            fo = open(sfn,'rt')
            twd = fo.read()
            fo.close
        self.twsf.delete(1.0, END)
        self.twsf.configure(fg = 'black', bg = 'white')
        self.twsf.insert(1.0,twd)
        self.twsf.grid(row=5, padx = 4, sticky = W)
        twd = ''
        ddfn = jfb + '.fdd'
        if ddfn in ls:
            fo = open(ddfn,'rt')
            twd = fo.read()
            fo.close
        self.twdd.delete(1.0,END)
        self.twdd.configure(fg = 'black', bg = 'white')
        self.twdd.insert(1.0,twd)
        self.twdd.grid(row=7, padx = 4, sticky = W)
        os.chdir(self.runDir)
        print('Profile {} Loaded'.format(jfb))    
        cl = ''  #Current Line
        while cl != 'END':
            p = sd.find('\n')
            cl = sd[:p]
            #print('cl = {}'.format(cl))
            sd = sd[p+1:]
            if len(cl) == 0:
                cl = 'END'
            if cl != 'END':
                try:
                    eval(cl)
                except:
                    e = sys.exc_info()
                    self.gStat('Error on eval()','black','red')
                    self.ome(e,'white','red')
        # the askopenfilename function always uses '/' as the dsc charater
        chop = pn.find('/')
        while chop != -1:
            pn = pn[chop+1:]
            chop = pn.find('/')
        pn = pn[:-4]
        print('Parsed screen display profile name = {}'.format(pn))
        self.gStat('Loaded Profile: {}'.format(pn))
        self.profileEntry.delete(0,END)
        self.profileEntry.insert(0,pn) 
        self.profileEntry.grid(row = 2, sticky = W)   
            
    def chooseFile(self):
        fn = filedialog.askopenfilename(parent = self,initialdir = self.runDir, title = 'Choose File', filetypes = (("all files","*"),("all files","*.*")))
        self.twsf.insert(END,fn + '\n')
        self.twsf.grid(row = 5, padx = 4, sticky = W)
        self.gStat('File {} added to Source Files'.format(fn))
        print('File {} added to Source Files'.format(fn))
        
    def startProp(self):
        ok = True
        twsfv = self.twsf.get("1.0",'end-1c')
        twddv = self.twdd.get(1.0,'end-1c')
        if len(twsfv) == 0:
            mb.showerror('No Source File', 'No Source File values entered.')
            ok = False
        elif len(twddv) == 0:
            mb.showerror('No Destination Dir', 'No Destination Directory values entered.')
            ok = False
        if ok:
            uc = 0  # Updated Count
            mc = 0  # Move Count
            ac = 0  # Already up to date Count
            ec = 0  # Error Count
            # Looping Through the Source Files
            swd = twsfv  # Source Work Data
            dwd = twddv  # Destination Work Data
            if self.runDir.find('/') < 0:
                # conver paths for windows OS
                print('Windows dsc convertion code entered.')
                t=swd
                swd = t.replace('/','\\')
                t = dwd
                dwd = t.replace('/','\\')
            print('\nStart Propagate Function called ---')
            twddv = dwd
            seld = swd.find('\n')  # Source End Line Detected
            while seld > -1:
                sf = swd[:seld]  # Source File (full path)
                swd = swd[seld+1:]
                if len(sf) == 0:  # I'll just ignore blank lines
                    seld = swd.find('\n')
                    continue
                bfn = sf  # Base File Name (or it will be soon)
                chop = bfn.find(self.dsc)
                while chop > -1:
                    bfn = bfn[chop+1:]  # Base Source File name only
                    chop = bfn.find(self.dsc)
                seld = swd.find('\n')
                print('** Processing Source file: {}'.format(bfn))  
                try:
                    fo = open(sf,'rb')
                except:
                    e = sys.exc_info()
                    print('Could not open to source file:\n{}'.format(sf))
                    print('Error:\n{}'.format(e))
                    self.gStat('{} Not Found','black','red')
                    ec += 1
                    mb.showerror('File not found:',sf)
                    continue
                print('Source file Opened')
                try:
                    sd = fo.read()  # Source Data
                except:
                    e = sys.exc_info()
                    print('Error Reading source file:\n{}'.format(e))
                    gStat('Error Reading source file!','black','red')
                    ec += 1
                    continue
                fo.close()
                print('Source file {} read sucessfully!'.format(bfn))
                sflmt = os.path.getmtime(sf)  # Source File Last Modified Time
                print('Source file timestamp: {}'.format(sflmt))
                its = int(sflmt)  # Integer Time Stamp
                print(dt.datetime.fromtimestamp(its).strftime('%Y-%m-%d %H:%M:%S'))
                dwd = twddv # need to reset dwd each pass of outer loop
                deld = dwd.find('\n')  # Destination End Line Detected
                while deld > -1:
                    dd = dwd[:deld]  #Destination dir 
                    dwd = dwd[deld+1:]
                    if len(dd) == 0:
                        deld = dwd.find('\n')
                        continue
                    print('Checking Destination Directory: {}'.format(dd))
                    fdn = dd + self.dsc + bfn  # Full Dest Name
                    try:
                        os.chdir(dd)
                    except:
                        e = sys.exc_info()
                        print('Error could not open to dest dir:\n{}'.format(fdn))
                        print('Error:\n{}'.format(e))
                        ec += 1
                        self.gStat('Destination Directory {} Not Found'.format(dd),'black','red')
                        mb.showerror('Directory not found:',dd)
                        continue
                    ls = os.listdir()
                    if bfn in ls:
                        dflmt = os.path.getmtime(fdn)
                        v = ' updated on '  # Verb
                        print('Destination file last modified timestame : {}'.format(dflmt))
                        its = int(dflmt)
                        print(dt.datetime.fromtimestamp(its).strftime('%Y-%m-%d %H:%M:%S'))
                    else:
                        print('File not yet in Destination directory.')
                        dflmt = 0.0
                        v = ' moved to '
                    #print('dd = {}  fdn = {}  sflmt = {}  dflmt = {}'.format(dd,fdn,sflmt,dflmt))
                    if sflmt > dflmt:
                        try:
                            fo = open(fdn,'wb')
                            fo.write(sd)
                            fo.close()
                        except:
                            e = sys.exc_info()
                            ec+=1
                            print('<< Error Opening Destination File>>\n{}'.format(e))
                            continue
                        m = '>> {}{}{}'.format(bfn,v,dd)
                        print(m)
                        if v.find('up') > -1:
                            uc += 1
                        else:
                            mc += 1
                        self.gStat(m,'black', 'green')
                    else:
                        m = '{} Up to date'.format(fdn)
                        print(m)
                        ac += 1
                        self.gStat(m,'black','Yellow')
            m = 'Created: {}  Updated: {}  Not Old: {}  Errors: {}'.format(mc,uc,ac,ec)
            print(m)
            self.gStat(m,'white','blue')
       
root = Tk() 
cd = os.getcwd()
if cd.find('/') > -1:
    root.geometry('840x360')  # linux Debian 10
else:
    root.geometry('790x260')  # Windows 10
app = win(root)
root.mainloop()

