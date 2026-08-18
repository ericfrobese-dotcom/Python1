# GUI TCP/IP Utility Project- plan to create Windows and Linux executables of this code 
from tkinter import *
from PIL import Image, ImageTk
from tkinter import filedialog
from tkinter import messagebox as mb
import socket
import threading
import queue as _queue
import os
import shutil
import datetime as dt
import getpass
import sys
#import time
import webbrowser
# now running from /home/eric/java/js-basics
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
        self.master.title("TCP/IP Utility")
        self.grid(row = 0)
        #quitButton = Button(self, text = 'Quit', command=self.client_exit)
        #quitButton.place(x=0, y=0)
        menu = Menu(self.master)
        self.master.config(menu=menu)
        file = Menu(menu)
        file.add_command(label='Load Profile', command = self.loadProfile)
        file.add_command(label='Save Profile', command = self.saveProfile)
        file.add_command(label='Exit', command = self.client_exit)
        menu.add_cascade(label='File', menu=file)
      
        tools = Menu(menu)
        #edit.add_command(label='Show Image',command=self.showImg)        
        tools.add_command(label='Send',command=self.sendMsg)
        tools.add_command(label='Listen',command=self.listenOnPort)
        menu.add_cascade(label='Tools', menu=tools)
        
        documentation = Menu(menu)
        documentation.add_command(label = 'View Documentation',command=self.viewDoc)
        menu.add_cascade(label = 'Documentation', menu = documentation)
        ipRegex = r'^[\d]{1,3}\.[\d]{1,3}+\.[\d]{1,3}+\.[\d]{1,3}+$'
        # The line below was causing an error on VS Community running in Windows 10, only used in 1 function so...
        #self.bmff = b''  #  Binary Message from file
        self.oa = ''  # ACK msg
        self.fn = ''
        self.df = 'TCP_IP Utility Documentation.pdf'  # Documentation File
        self.destDir = ''
        self.runDir = os.getcwd()  # Run Dir
        self.dsc = '/' if self.runDir.find('\\')<0 else '\\'
        #print('self.dsc = {}'.format(self.dsc))
        # need to tie down a save dir in DEBIAN
        # 5/1/21 changing to look for /etc/apt
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
                if 'tup' not in ls:
                    os.mkdir('tup')
                    fp = dn + self.dsc + self.df
                    print('Full Path to Documentation file:\n{}  occurance 1'.format(fp))
                    try:
                        shutil.move(fp, dn+'/tup')
                    except:
                        e = sys.exc_info()
                        print('Could not install Documentation file, Error:\n{}'.format(e))
                self.tupPath = dn +'/tup'
                # Check Documentation file
                ls = os.listdir(self.tupPath)
                if self.df not in ls:
                    try:
                        shutil.move(self.runDir + self.dsc + self.df, self.tupPath)
                    except:
                        e = sys.exc_info()
                        print('Could not install Documentation file, Error:\n{}\nOccurance 2'.format(e))
                        print('File w/ path: {}'.format(self.runDir + self.dsc + self.df))
                        print('Destination: {}'.format(self.tupPath))
        else:
            self.tupPath = self.runDir + self.dsc + 'tup'  # TCP Util Profile Path
        #print('debian = {}  self.tupPath = {}'.format(debian,self.tupPath))
        # Maybe create data save directory
        os.chdir(self.runDir)
        ls = os.listdir()
        print('ls : {}'.format(ls))
        if 'tup' not in ls:
            os.mkdir('tup')  #File Propagate Data
            try:
                shutil.move(self.tupPath + self.dsc + self.df , self.tupPath)
            except:
                        e = sys.exc_info()
                        print('Could not install Documentation file, Error:\n{}\nOccurence 3'.format(e))
        # Rows 1 and 2
        self.label_oip = Label(self, text = "Send to IP")
        self.label_oip.grid(row = 1, sticky = E)
        self.oipEntry = Entry(self, width = 15)
        self.oipEntry.grid(row =1, column = 1, sticky = W)
        self.label_op = Label(self, text = 'Send to port')
        self.label_op.grid(row = 2, column = 0,  sticky = E)
        self.opEntry = Entry(self, width = 5)
        self.opEntry.grid(row = 2, column = 1, sticky = W)
        self.loadProfileButton = Button(self, text = 'Load Profile', command = self.loadProfile)
        self.loadProfileButton.grid(row = 1, column = 1, sticky = E)
        self.labelProfile = Label(self, text = 'Profile')
        self.labelProfile.grid(row=1, column = 1, pady = 4, sticky = N)
        self.profileEntry = Entry(self, width = 25)
        self.profileEntry.grid(row = 2, column=1, pady = 4, sticky = S)
        self.SaveProfileButton = Button(self, text = 'Save Profile', command = self.saveProfile)
        self.SaveProfileButton.grid(row = 2, column = 1, sticky = E)
        # Row 3
        self.label_cf = Label(self, text = "Load msg from file:")
        self.label_cf.grid(row = 3, column = 0)
        self.fnEntry = Entry(self, width = 80)
        self.fnEntry.grid(row = 3, column = 1, sticky = W)
        self.bb = Button(self,text = "Browse", command = self.chooseFile)
        self.bb.grid(row = 3, column = 1, sticky = E) 
                     #column = 2, sticky = W)
        # Row 4 <<Status line>>
        self.status = StringVar()
        self.status_label = Label(self,bg='black',fg='white', textvariable = self.status)
        self.status.set(' -- General Status Info --')
        self.status_label.grid(row = 4, column = 1)
        # Row 5 - Outbound Message
        self.cb_sfn_var = IntVar()
        self.cb_sfn = Checkbutton(self, text="Add File Name", variable = self.cb_sfn_var)
        self.cb_sfn.grid(row = 5, column = 0, sticky = W)
        self.twom = Text(self, height = 6, width = 80)  # Text Widget Outbound Message
        self.twom.grid(row = 5, column = 1, sticky = W)
        self.sendButton = Button(self, text = 'Send', command = self.sendMsg)
        self.sendButton.grid(row = 5, column = 2, sticky = W)
        # Row 6 Ack Received for Outbound Message
        self.cb_getAck_var = IntVar()
        self.cb_getAck = Checkbutton(self, text = 'Read ACK', variable = self.cb_getAck_var)
        self.cb_getAck.grid(row = 6)
        self.twAckRec = Text(self,height = 3, width = 80)  # Text Widget ACK Received
        self.twAckRec.grid(row = 6, column = 1, sticky = W)
        # Row 7  Inbound status ()
        self.inStatus = StringVar()
        self.inboundLabel = Label(self, fg = 'white', bg = 'black', textvariable = self.inStatus)
        self.inStatus.set(' -- Inbound Status Info --')
        self.inboundLabel.grid(row = 7, column = 1)
        # Row 8  Listening Port
        self.ipLabel = Label(self, text = 'Listen on Port')
        self.ipLabel.grid(row = 8,sticky = E)
        self.ipEntry = Entry(self, width = 5)
        self.ipEntry.grid(row = 8, column = 1, sticky = W)
        # Row 9 Inbound message
        self.cb_rfn_var = IntVar()
        self.cb_rfn = Checkbutton(self, text = 'Read File Name', variable = self.cb_rfn_var)
        self.cb_rfn.grid(row = 9, sticky = W)
        self.twim = Text(self, height = 6, width = 80)  # Text Widget Inbound Message
        self.twim.grid(row = 9, column = 1, sticky = W)
        self.listenButton = Button(self, text = 'Listen', command = self.listenOnPort)
        self.listenButton.grid(row = 9, column = 2, sticky = W)
        # Row 10 ACK sent for Inbound Message
        self.cb_sendAck_var = IntVar()
        self.cb_sendAck = Checkbutton(self,text = 'Send ACK', variable = self.cb_sendAck_var)
        self.cb_sendAck.grid(row = 10)
        self.twia = Text(self, height = 3, width = 80)  # Text Widget Inbound ACK
        self.twia.grid(row = 10, column = 1, sticky = W)
        # Row 11  Destination Directory
        self.destDirLabel = Label(self, text = 'Destination Directory')
        self.destDirLabel.grid(row=11, sticky = W)
        self.destDirEntry = Entry(self, width = 80)
        self.destDirEntry.grid(row = 11, column = 1, sticky = W)
        self.selectDirButton = Button(self, text = 'Browse', command = self.selectDir)
        self.selectDirButton.grid(row=11, column = 2, sticky = W)
        # Row 12 Save as File name
        self.fnOutLabel = Label(self, text = 'Save File Name')
        self.fnOutLabel.grid(row=12, sticky = W)
        self.fnOutEntry = Entry(self, width = 60)
        self.fnOutEntry.grid(row=12, column = 1, sticky = W)
        self.saveFileButton = Button(self, text = 'Save Inbound File', command = self.saveFile)
        self.saveFileButton.grid(row=12, column = 2, sticky = W)

    def ome(self, msg , f = 'white', b = 'red'):  # Outbound Message Error
        self.twAckRec.delete(1.0,END)
        self.twAckRec.configure(fg = f, bg = b)
        self.twAckRec.insert(1.0,msg)
        self.twAckRec.grid(row = 6, column = 1, sticky = W)
        
    def ime(self, msg , f = 'white', b = 'red'):  # Outbound Message Error
        self.twim.delete(1.0,END)
        self.twim.configure(fg = f, bg = b)
        self.twim.insert(1.0,msg)
        self.twim.grid(row = 9, column = 1, sticky = W)

    def gStat(self, msg, f = 'white', b = 'black'):
        self.status.set(msg)
        self.status_label.config(bg = b, fg = f)
        self.status_label.grid(row = 4, column = 1)
        
    def iStat(self, msg, f = 'white', b = 'black'):
        self.inboundLabel.config(bg = b, fg = f)
        self.inStatus.set(msg)
        self.inboundLabel.grid(row = 7, column = 1)
        
    def viewDoc(self):
        fn = self.df  # Documentation File
        #c = os.getcwd()
        # may need to move documentation file to data dir
        ls = os.listdir(self.tupPath)
        found = fn in ls
        if not found:
            ls = os.listdir(self.runDir)
            if fn in ls:
                shutil.move(self.runDir + self.dsc + self.df, self.tupPath)
            else:
                mb.showerror('Documentation file Missing',"Can not find document file, sorry.")
                self.gStat('Documentation file "{}" not found in data directory.'.format(fn),'black','red')
                return
        if self.dsc == '/':
            fp = self.tupPath + '/' + fn  # Full Path doc file
            webbrowser.open(r'file:{}'.format(fp))
        else:
            c = os.getcwd()
            os.chdir(self.tupPath)
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
            # Accept normal profile names (including spaces and punctuation)
            # and add .tup when it is not already present.
            if not pn.lower().endswith('.tup'):
                pn = pn + '.tup'
            pfn = self.tupPath + self.dsc + pn  #full Profile File Name 
            # Handle Text Widgets up front will save to different ext off base profile name
            bfn = pfn[:-4]
            twomv = self.twom.get("1.0",'end-1c')
            if len(twomv) > 0:
                omfn = bfn + '.tom' # tcp Outbound Message File Name
                fo = open(omfn,'wt')
                fo.write(twomv)
                fo.close()
            twoav =  self.twAckRec.get(1.0,'end-1c')
            if len(twoav) > 0:
                oafn = bfn + '.toa'  # tcp Outbound Ack File Name
                fo = open(oafn,'wt')
                fo.write(twoav)
                fo.close()
            twimv = self.twim.get(1.0,'end-1c')
            if len(twimv) > 0:
                imfn = bfn + '.tim'
                fo = open(imfn,'wt')
                fo.write(twimv)
                fo.close()
            twiav = self.twia.get(1.0,'end-1c')
            if len(twiav) > 0:
                iafn = bfn + '.tia'  # tcp Inbound Ack File Name
                fo = open(iafn,'wt')
                fo.write(twiav)
                fo.close()
            sd = ''
            oip = self.oipEntry.get()
            if len(oip)>0:
                sd = 'self.oipEntry.delete(0,END)\n'
                sd = sd + 'self.oipEntry.insert(0, "{}")\n'.format(oip)
                sd = sd + 'self.oipEntry.grid(row=1, column=1, sticky =W)\n'
            op = self.opEntry.get()
            if len(op)>0:
                sd = sd + 'self.opEntry.delete(0,END)\n'
                sd = sd + 'self.opEntry.insert(0, "{}")\n'.format(op)
                sd = sd + 'self.opEntry.grid(row=2, column=1, sticky = W)\n'
            fev = self.fnEntry.get()  # Filename Entry Value
            if len(fev)>0:
                sd = sd + 'self.fnEntry.delete(0,END)\n'
                sd = sd +'self.fnEntry.insert(0, "{}")\n'.format(fev)
                sd = sd + 'self.fnEntry.grid(row=3, column=1, sticky=W)\n'
            cb_sfn = self.cb_sfn_var.get()
            sd = sd + 'self.cb_sfn_var.set({})\n'.format(cb_sfn)
            sd = sd + 'self.cb_sfn.grid(row=5, sticky = W)\n'
            cb_afn = self.cb_sfn_var.get()  # Command Button Add File Name
            sd = sd + 'self.cb_sfn_var.set({})\n'.format(cb_afn)
            sd = sd + 'self.cb_sfn.grid(row=5, sticky=W)\n' 
            cb_ga = self.cb_getAck_var.get()
            sd = sd + 'self.cb_getAck_var.set({})\n'.format(cb_ga)
            sd = sd + 'self.cb_getAck.grid(row=6)\n'
            lopv = self.ipEntry.get()  # Listen On Port Value
            if len(lopv)>0:
                sd = sd + 'self.ipEntry.delete(0,END)\n'
                sd = sd + 'self.ipEntry.insert(0,"{}")\n'.format(lopv)
                sd = sd + 'self.ipEntry.grid(row=8, column=1, sticky=W)\n'
            cb_rfn = self.cb_rfn_var.get()
            sd = sd + 'self.cb_rfn_var.set("{}")\n'.format(cb_rfn)
            sd = sd + 'self.cb_rfn.grid(row=9, sticky=W)\n'
            cb_sav = self.cb_sendAck_var.get()
            sd = sd + 'self.cb_sendAck_var.set("{}")\n'.format(cb_sav)
            sd = sd + 'self.cb_sendAck.grid(row=10)\n'
            ddv = self.destDirEntry.get()
            if len(ddv)>0:
                sd = sd + 'self.destDirEntry.delete(0,END)\n'
                sd = sd + 'self.destDirEntry.insert(0,"{}")\n'.format(ddv)
                sd = sd + 'self.destDirEntry.grid(row=11, column=1,sticky=W)\n'
            sfn = self.fnOutEntry.get()
            if len(sfn)>0:
                sd = sd + 'self.fnOutEntry.delete(0,END)\n'
                sd = sd + 'self.fnOutEntry.insert(0,"{}")\n'.format(sfn)
                sd = sd + 'self.fnOutEntry.grid(row=12,column=1, sticky = W)\n'
            sd = sd + 'END\n'
        #print('twomv = {}'.format(twomv))
        #print('savesd:\n{}'.format(sd))
        try:
            fo = open(pfn, 'wt')
            fo.write(sd)
            fo.close()
        except Exception as e:
            self.gStat('Error saving profile: {}'.format(e), 'black', 'red')
            mb.showerror('Save Profile Error',
                         'Could not save profile:\n{}\n\n{}'.format(pfn, e))
            return
        self.gStat('Profile {} Saved.'.format(pn))
    
    def saveFile(self):
        ok = True
        twomv = self.twim.get("1.0",'end-1c')
        destDir = self.destDirEntry.get()
        fnOut = self.fnOutEntry.get()
        os.chdir(destDir)
        ls = os.listdir()
        if len(twomv) == 0:
            mb.showerror('No File data', 'No inbound file loaded to Save')
            ok = False
        elif len(destDir) == 0:
            mb.showerror('"Destination Dir" vale missing', 'Enter the Destination Directory value')
            ok = False
        elif len(fnOut) == 0:
            mb.showerror('Missing Save file name','Please enter the "Save file name" value')
            ok = False
        elif fnOut in ls:
            ok = mb.askyesno('Warning File Exists!','Overwrite File {}?'.format(fnOut),default = 'no')
        if ok:
            self.gStat('Saving File')
            # dsc = '/' if destDir.find('/') > -1 else '\\'  # Directory Separator Character
            ofn = destDir + self.dsc + fnOut  # Outbound File Name
            wd = twomv.encode()
            fo = open(ofn,'wb')
            fo.write(wd)
            fo.close()
            msg = 'Saved: {}'.format(ofn)
            #print(msg)
            self.gStat(msg)
    
    def selectDir(self):
        cwd = os.getcwd()
        self.destDir = filedialog.askdirectory(parent = self, initialdir = cwd, title = 'Select Directory')
        self.destDirEntry.delete(0,END)
        self.destDirEntry.insert(0, self.destDir)
        self.destDirEntry.grid(row = 11, column = 1, sticky = W)
        #self.triggerRefresh()
    
    def loadProfile(self):
        # Load Values Section
        # load in any save data (starting off just using a file)
        pn = filedialog.askopenfilename(
            initialdir=self.tupPath,
            title='Select Profile',
            filetypes=(("Profiles", "*.tup"), ("all files", "*.*"))
        )

        # Some Tk/file-dialog environments can return an empty value or,
        # unexpectedly, a tuple.  Do not attempt to open either as a path.
        if isinstance(pn, (tuple, list)):
            pn = pn[0] if pn else ''
        if not isinstance(pn, (str, bytes, os.PathLike)) or not pn:
            self.gStat('Profile load cancelled.')
            return

        twd = ''  # Text Widget Data
        ldscp = len(pn)  # Last Directory Separator Character Position
        #might not have selected a file..
        if ldscp > 0:
            ldscp -= 1
            while pn[ldscp] != '/':
                ldscp -= 1
            self.tupPath = pn[:ldscp]
        fo = open(pn,'rt')
        sd = fo.read()  # Saved Data 
        fo.close()
        bf = pn[:-4]
        # bf includes full path, need to remove path for value to check in direcotry..
        jfb = bf  # just file base w/out path (or extention)
        # EJF 10/17/20 - filedialog.askopenfilename returns / as it's dsc value in both window and linux
        chop = jfb.find('/')
        while chop != -1:
            jfb = jfb[chop+1:]
            chop = jfb.find('/')
        #print('loadProfile bf = {}  jf = {}'.format(bf,jfb))
        os.chdir(self.tupPath)
        ls = os.listdir()  # Array with current directoery (like the linux BASH command)
        #omfn = bf + '.tom'  since we are now in tup dir don't need full path
        jf = jfb + '.tom'
        #print('jf = {}  in ls = {}'.format(jf, jf in ls))
        if jf in ls:
            fo = open(jf,'rt')
            twd = fo.read()
            fo.close()
        self.twom.delete(1.0, END)
        self.twom.insert(1.0, twd)
        self.twom.grid(row = 5, column = 1, sticky = W)
        # re-using twd for all text widget fields on screen
        twd = ''
        oafn = jfb + '.toa'
        if oafn in ls:
            fo = open(oafn,'rt')
            twd = fo.read()
            fo.close
        self.twAckRec.delete(1.0, END)
        self.twAckRec.configure(fg = 'black', bg = 'white')
        self.twAckRec.insert(1.0,twd)
        self.twAckRec.grid(row=6, column = 1, sticky = W)
        twd = ''
        imfn = jfb + '.tim'
        if imfn in ls:
            fo = open(imfn,'rt')
            twd = fo.read()
            fo.close
        self.twim.delete(1.0,END)
        self.twim.configure(fg = 'black', bg = 'white')
        self.twim.insert(1.0,twd)
        self.twim.grid(row=9, column=1, sticky = W)
        twd = ''
        iafn = jfb + '.tia'
        if iafn in ls:
            fo = open(iafn,'rt')
            twd = fo.read()
            fo.close()
        self.twia.delete(1.0,END)
        self.twia.insert(1.0,twd)
        self.twia.grid(row = 10, column=1, sticky = W)
        os.chdir(self.runDir)
        #self.triggerRefresh()
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
                    self.ome(e,'black','red')
        print('Full profile name:\n{}'.format(pn))
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
        self.profileEntry.grid(row = 2, column=1, sticky = S)   
            
    def chooseFile(self):
        self.fn = filedialog.askopenfilename(parent = self,initialdir = self.runDir, title = 'Choose File', filetypes = (("all files","*"),("all files","*.*")))
        self.fnEntry.delete(0,END)
        self.fnEntry.grid(row = 3, column = 1, sticky = W)
        fo = open(self.fn,'rb')  # File Object
        try:
            bmff = fo.read()  #  Binary Message from file
            tv = bmff.decode()  #  Text Version
            self.twom.delete(1.0,END)
            self.twom.insert(END, tv)
            self.twom.grid(row = 5, column = 1, sticky = W)
            self.gStat('File {} loaded into Outbound Box'.format(self.fn))
            self.fnEntry.insert(0, self.fn)
            print('self.fnEntryVar set to {}'.format(self.fn))
            self.fnEntry.grid(row = 3, column = 1, sticky = W)
        except UnicodeDecodeError as e:
            print(e)
            msg = 'UnicodeDecodeError: {}'.format(e)
            self.gStat(msg,'black','red')
        except:
            e = sys.exc_info()
            msg = 'Error occured; file NOT Loaded!'
            print(e)
            self.gStat(msg,'black','red')
        
    def sendMsg(self):
        ok = True
        twomv = self.twom.get("1.0",'end-1c')
        if len(self.oipEntry.get()) == 0:
            mb.showerror('"Send to" Ip Address missing', 'Enter the IP address of the listening application')
            ok = False
        elif len(self.opEntry.get()) == 0:
            mb.showerror('"Send to" Port vale missiing', 'Enter the outbound port value')
            ok = False
        elif len(twomv) == 0:
            mb.showerror('Missing Message','No message data to send')
            ok = False
        if ok:
            self.twAckRec.delete('1.0',END)
            self.twAckRec.configure(fg = 'black', bg = 'white')
            #print('sendMsg entered')
            #self.twAckRec.grid(row = 6, column = 1, sticky = W)
            if twomv[0] == chr(11):
                twomv = twomv[1:]
            fni = self.cb_sfn_var.get()  # file name integer
            if fni == 1:
                twomv = '{}filename: {}\n'.format(chr(11),self.fn) + twomv
            if twomv.find(chr(13)) == -1:
                ov = twomv.replace('\n','\r')  #outbound value
            else:
                ov = twomv
            ov = chr(11) + ov
            if ov[-1] != '\r':
                ov = ov + '\r'
            if ov.find(chr(28))==-1:
                ov = ov + chr(28) + '\r'
            br = ov.encode()  # Binary Result
            #ba = bytearray(br)
            oip = self.oipEntry.get()
            op = int(self.opEntry.get())
            ip_n_port = (oip,op)
            #print('Preparing to open port.')
            self.gStat('Opening to {}'.format(ip_n_port))
            o_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                o_sock.connect(ip_n_port)
            except ConnectionRefusedError as e:
                print('o_sock.connect can\'t open to listening port e:\n{}'.format(e))
                self.gStat('Error on socket.connect; ensure listener is up listening on port','black','red')
                self.ome(e,'black','red')
                return
            except:
                self.gStat('Error on socket.connect','black','red')
                e = sys.exc_info()
                self.ome(e,'black','red')
                return
            self.gStat('Connected, Sending...','white','green')
            try:
                    o_sock.sendall(br)
                    self.gStat('Message Sent','white', 'green')
            except:
                e = sys.exc_info()
                self.gStat('Error on socket.sendall','black','red')
                self.ome(e,'black','red')
            getAck = self.cb_getAck_var.get() == 1
            if getAck:
                ack = ''
                self.iStat('Getting the ACK', 'white', 'green')
                self.twAckRec.delete(1.0,END)
                fullAck = ''
                cts = dt.datetime.now()  # Current Time Stamp
                cqt = cts + dt.timedelta(0,20)  # Check Quit Time
                while fullAck.find(chr(28)) == -1:
                    try:
                        ack = o_sock.recv(1000)
                        fullAck = fullAck + ack.decode()
                        self.iStat(' >> ACK Received <<', 'white', 'green')
                    except:
                        e = sys.exc_info()
                        self.iStat('Error on socket.receive','black','red')
                        self.ime(e,'black','red')
                        fullAck = fullAck + chr(28)
                    cts = dt.datetime.now()
                    if cts > cqt:
                        ans = mb.askyesno('No ACK sent','Abort ACK Receive attempt?', default = 'yes')
                        if ans: 
                            fullAck = fullAck + chr(28)
                            self.iStat('>> ACK listen Aborted <<','black','orange')
                        else:
                            cqt += dt.timedelta(0,40)
                self.twAckRec.insert(1.0,fullAck)
                self.twAckRec.grid(row = 6, column = 1, sticky = W)
            o_sock.close()
            print('Socket closed')
            
    def buildAck(self):
        print('buildAck funtion entered')
        self.gStat('Building ACK...')
        im = self.twim.get(1.0, END)  # Inound Message
        sp = im.find('MSH')  # Starting Position
        if sp == -1: 
            self.gStat('Not an HL7 Message, can not create an ACK','black','orange')
            return False
        #self.triggerRefresh()
        cts = dt.datetime.now()  # Current Time Stamp
        # may need to zero pad most date time values..
        ms = str(cts.month)  # Month Strig
        if len(ms)<2: ms = '0' +ms
        dys = str(cts.day)  # Day String
        if len(dys)<2: dys = '0'+dys
        hs = str(cts.hour)  # Hour String
        if len(hs)<2: hs= '0' + hs
        mns = str(cts.minute)  # Minute String
        if len(mns)<2: mns = '0' + mns
        ss = str(cts.second)
        if len(ss)<2: ss = '0' + ss
        adt = str(cts.year) + ms + dys + hs + mns + ss  # ACK Date Time
        #print('adt (Ack Date Time) set to {}'.format(adt))
        subs = im[sp:]  # sub String
        ep = subs.find(chr(13))
        msh = subs[:ep]
        #print('msh = {}'.format(msh))
        ml = list(msh.split('|'))  # MSH List
        smcid = ml[9]  # Sent Message Control ID
        #print('smcid = {}'.format(smcid))
        oa = chr(11) + 'MSH|^~\&|TCP/IP Utilites|' + ml[2] + '||' + adt + '||ACK|'+ str(cts)
        oa = oa + '|' + ml[10] +'|' + ml[11] +'\rMSA|AA|' + smcid + '|Message Received\r'+chr(28)+'\r'
        #print('oa = {}'.format(oa))
        self.oa = oa  # Outbound ACK
        return True

    def listenOnPort(self):
        ipv = self.ipEntry.get()
        if len(ipv) == 0:
            mb.showerror('\"Listen on\" port value missing', 'Please enter the Listening Port value')
            return
        try:
            port = int(ipv)
        except Exception:
            mb.showerror('Invalid port', 'Enter a numeric port value')
            return
        # create inter-thread queue and stop event
        self.listener_queue = _queue.Queue()
        self.listener_stop = threading.Event()
        send_ack = True if self.cb_sendAck_var.get() == 1 else False
        # start listener thread
        self.listener_thread = threading.Thread(target=self._listener_thread_main, args=(port, self.listener_queue, self.listener_stop, send_ack), daemon=True)
        self.listener_thread.start()
        self.listenButton.config(text='Stop', command=self.stop_listener)
        self.status.set(f'Started listener on 0.0.0.0:{port}')
        self.status_label.config(bg='green', fg='white')
        # start polling queue
        self.after(200, self._poll_listener_queue)

    def _poll_listener_queue(self):
        try:
            while True:
                try:
                    item = self.listener_queue.get_nowait()
                except _queue.Empty:
                    break
                if not item:
                    continue
                if isinstance(item, tuple) and item[0] == '__error__':
                    self.status.set('Listener error: ' + str(item[1]))
                    continue
                data, addr = item
                # process incoming on main thread
                self._process_incoming_ui(data, addr)
        except Exception:
            # ignore transient errors
            pass
        # if thread still running, schedule another poll
        if getattr(self, 'listener_thread', None) and self.listener_thread.is_alive():
            self.after(200, self._poll_listener_queue)
        else:
            # ensure UI button reset
            self.listenButton.config(text='Listen', command=self.listenOnPort)
            self.status.set('Listener stopped')
            self.status_label.config(bg='blue', fg='white')

    def stop_listener(self):
        if getattr(self, 'listener_thread', None) and self.listener_thread.is_alive():
            self.listener_stop.set()
            self.status.set('Stopping listener...')
            self.listenButton.config(state='disabled')
            # give thread a moment to exit
            self.after(500, self._finish_stop)
        else:
            self.status.set('Listener not running')

    def _finish_stop(self):
        try:
            if getattr(self, 'listener_thread', None):
                self.listener_thread.join(timeout=0.5)
        except Exception:
            pass
        self.listenButton.config(text='Listen', command=self.listenOnPort, state='normal')
        self.status.set('Listener stopped')
        self.status_label.config(bg='blue', fg='white')

    def _process_incoming_ui(self, data, client_address):
        # replicate the original per-message handling from listenOnPort's loop
        try:
            rfnv = self.cb_rfn_var.get()
            data_body = data
            if rfnv == 1:
                sp = data.find('filename:')
                if sp != -1:
                    sp += 10
                    ep = data.find('\n')
                    if ep == -1:
                        ep = data.find('\r')
                    ofn = data[sp:ep] if ep != -1 else data[sp:]
                    nep = data.find(chr(28))
                    if nep != -1:
                        data_body = data[ep+1:nep] if ep != -1 else data[:nep]
                    else:
                        data_body = data[ep+1:] if ep != -1 else data
                    dsc = '/' if ofn.find('/') > -1 else '\\'
                    chop = ofn.find(dsc)
                    while chop > -1:
                        ofn = ofn[chop+1:]
                        chop = ofn.find(dsc)
                    self.fnOutEntry.delete(0,END)
                    self.fnOutEntry.insert(0,ofn)
            self.twim.delete(1.0,END)
            self.twim.configure(fg = 'black', bg = 'white')
            self.twim.insert(1.0,data_body)
            self.twim.grid(row = 9, column = 1, sticky = W)
            self.iStat(f'Message received from {client_address}','white','green')
        except Exception as e:
            self.iStat(f'Error processing incoming: {e}','black','red')

    def _listener_thread_main(self, port, out_queue, stop_event, send_ack):
        """Threaded listener: accepts connections (with a short timeout), reads until record separator (chr(28)),
        and puts (data, client_addr) tuples on the provided out_queue for the GUI thread to process.
        """
        import socket
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('0.0.0.0', port))
            sock.listen(1)
            sock.settimeout(1.0)
        except Exception as e:
            out_queue.put(('__error__', f'Failed to bind/listen: {e}'))
            return
        while not stop_event.is_set():
            try:
                try:
                    conn, client_addr = sock.accept()
                except socket.timeout:
                    continue
                except Exception as e:
                    out_queue.put(('__error__', f'Accept error: {e}'))
                    continue
                # receive until record separator or connection closed
                data = ''
                conn.settimeout(1.0)
                while True:
                    if stop_event.is_set():
                        break
                    try:
                        chunk = conn.recv(4096)
                    except socket.timeout:
                        continue
                    except Exception as e:
                        out_queue.put(('__error__', f'Recv error: {e}'))
                        break
                    if not chunk:
                        break
                    try:
                        s = chunk.decode()
                    except Exception:
                        s = chunk.decode(errors='ignore')
                    data += s
                    if chr(28) in s:
                        break
                # hand off to UI thread
                out_queue.put((data, client_addr))
                if send_ack:
                    try:
                        conn.sendall(b'ACK')
                    except Exception:
                        pass
                try:
                    conn.close()
                except Exception:
                    pass
            except Exception as e:
                out_queue.put(('__error__', str(e)))
        try:
            sock.close()
        except Exception:
            pass

    def client_exit(self):
        root.destroy()
       
root = Tk() 
cd = os.getcwd()
if cd.find('/') > -1:
    root.geometry('950x555')  # linux Debian 10
else:
    root.geometry('870x520')  # Windows 10
app = win(root)
root.mainloop()

