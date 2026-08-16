# GUI File Utility Project- plan to create Windows and Linux executables of this code 
from tkinter import *
from tkinter import filedialog
from tkinter import messagebox as mb
from tkinter import ttk
import os
import shutil
import getpass
import datetime as dt
import webbrowser
import re
import urllib.parse as up
import threading
import queue
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
        # Add Source Dir button for sink option
        self.sdButton = Button(self, text = 'Add Source Dir', command = self.selectSourceDir)
        self.sdButton.grid(row = 5, column = 2, sticky = W)
        self.twsf = Text(self, height = 3, width = 80)  # Text Widget Source Files / Dir
        self.twsf.grid(row = 5, padx = 4, sticky = W)        
        # Row 7 - Destination Directory List
        self.ddButton = Button(self, text = 'Add Destination Dir', command = self.selectDir)
        self.ddButton.grid(row = 7, column = 1, sticky = W)
        self.twdd = Text(self, height = 6, width = 80)  # Text Widget Inbound Message
        self.twdd.grid(row = 7, padx = 4, sticky = W)
        # Sink option checkbox
        self.sink_var = IntVar(value=0)
        self.sink_cb = Checkbutton(self, text='Sink entire source directory to each destination', variable=self.sink_var)
        self.sink_cb.grid(row=6, column=1, columnspan=2, sticky=W)
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
        # Try to open the directory chooser rooted at common mount points so attached devices are shown
        cwd = os.getcwd()
        user = getpass.getuser()
        candidates = [cwd, f"/run/media/{user}", f"/media/{user}", "/mnt", "/"]
        initial = cwd
        for c in candidates:
            if os.path.exists(c):
                initial = c
                break
        dd = filedialog.askdirectory(parent=self, initialdir=initial, title='Select Directory (mounted devices may appear under /run/media or /media)')
        if not dd:
            # user cancelled
            return
        # normalize path
        dd = os.path.normpath(dd)
        self.twdd.insert(END, dd + '\n')
        self.twdd.grid(row=7, padx=4, sticky=W)
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
        if not fn:
            return
        self.twsf.insert(END,fn + '\n')
        self.twsf.grid(row = 5, padx = 4, sticky = W)
        self.gStat('File {} added to Source Files'.format(fn))
        print('File {} added to Source Files'.format(fn))

    def selectSourceDir(self):
        cwd = os.getcwd()
        sd = filedialog.askdirectory(parent=self, initialdir=cwd, title='Select Source Directory')
        if not sd:
            return
        sd = os.path.normpath(sd)
        # mark as source dir in twsf with a prefix so older behavior still works
        self.twsf.insert(END, '[DIR] ' + sd + '\n')
        self.twsf.grid(row = 5, padx = 4, sticky = W)
        self.gStat('Source directory {} added to Source list'.format(sd))
        print('Source directory {} added to Source list'.format(sd))
        
    def _normalize_destination(self, dd):
        """Normalize destination string. Support mtp:// URIs by resolving gvfs mount under /run/user/<uid>/gvfs.
        Returns a filesystem path if resolvable, otherwise returns original dd unchanged.
        """
        if not dd:
            return dd
        dd = dd.strip()
        # handle mtp URI variants
        if dd.lower().startswith('mtp:'):
            # remove leading scheme
            rest = re.sub(r'^mtp:\/\/?', '', dd, flags=re.IGNORECASE)
            parts = rest.split('/', 1)
            host = parts[0]
            subpath = parts[1] if len(parts) > 1 else ''
            # decode percent-encodings
            host_dec = up.unquote(host)
            sub_dec = up.unquote(subpath)
            # search gvfs mounts for matching host
            uid = os.getuid()
            gvfs_root = f"/run/user/{uid}/gvfs"
            if os.path.isdir(gvfs_root):
                try:
                    for entry in os.listdir(gvfs_root):
                        entry_dec = up.unquote(entry)
                        if 'mtp' in entry.lower() and host_dec in entry_dec:
                            candidate = os.path.join(gvfs_root, entry, *sub_dec.split('/')) if sub_dec else os.path.join(gvfs_root, entry)
                            candidate = os.path.normpath(candidate)
                            return candidate
                except Exception:
                    pass
            # fallback: try common gvfs path under home
            homegvfs = os.path.expanduser('~/.gvfs')
            if os.path.isdir(homegvfs):
                try:
                    for entry in os.listdir(homegvfs):
                        entry_dec = up.unquote(entry)
                        if 'mtp' in entry.lower() and host_dec in entry_dec:
                            candidate = os.path.join(homegvfs, entry, *sub_dec.split('/')) if sub_dec else os.path.join(homegvfs, entry)
                            return os.path.normpath(candidate)
                except Exception:
                    pass
            # couldn't resolve
            return dd
        else:
            return dd

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
            # If sink option selected, look for a source directory entry
            sink_mode = bool(self.sink_var.get())
            source_dir = None
            swd = twsfv
            # detect [DIR] lines in source list
            lines = [l for l in swd.splitlines() if l.strip()]
            for l in lines:
                if l.startswith('[DIR]'):
                    source_dir = l[6:].strip()
                    break
            if sink_mode and not source_dir:
                mb.showerror('No Source Directory', 'Sink mode selected but no source directory provided. Use Add Source Dir.')
                return
            # If sink_mode is enabled, perform directory sync for each destination
            if sink_mode and source_dir:
                # prepare destination list
                dlines = [l for l in twddv.splitlines() if l.strip()]
                dests = []
                for dd in dlines:
                    dd_res = self._normalize_destination(dd)
                    dd_use = dd_res if dd_res != dd and os.path.isdir(dd_res) else dd
                    if dd.lower().startswith('mtp:') and dd_res == dd:
                        print('Skipping MTP destination not mounted: {}'.format(dd))
                        continue
                    if not os.path.isdir(dd_use):
                        print('Destination not a dir: {}'.format(dd_use))
                        continue
                    dests.append(dd_use)
                if not dests:
                    mb.showerror('No valid Destinations', 'No valid destination directories to sync to. Ensure devices are mounted.')
                    return
                # count total files for progress
                total_files = 0
                for _root, _dirs, files in os.walk(source_dir):
                    total_files += len(files)
                # start background thread to perform sync and show progress UI
                self._start_sync_thread(source_dir, dests, total_files)
                return

            # Otherwise, original per-file behavior
            uc = 0
            mc = 0
            ac = 0
            ec = 0
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
                # ignore [DIR] entries when not in sink mode
                if sf.startswith('[DIR]'):
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
                    seld = swd.find('\n')
                    continue
                print('Source file Opened')
                try:
                    sd = fo.read()  # Source Data
                except:
                    e = sys.exc_info()
                    print('Error Reading source file:\n{}'.format(e))
                    gStat('Error Reading source file!','black','red')
                    ec += 1
                    seld = swd.find('\n')
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
                    # normalize destination (supports mtp:// URIs via gvfs)
                    dd_res = self._normalize_destination(dd)
                    if dd_res != dd and os.path.isdir(dd_res):
                        dd_use = dd_res
                    else:
                        dd_use = dd
                    # If the normalized looks like an mtp URI and didn't resolve, warn user
                    if dd.lower().startswith('mtp:') and dd_res == dd:
                        print('Error: MTP path provided but device mount not found for: {}'.format(dd))
                        ec += 1
                        self.gStat('MTP device not mounted or not accessible: {}'.format(dd),'black','red')
                        mb.showerror('MTP device not mounted', f"Could not resolve MTP path: {dd}\nPlease open the device in your file manager so it is mounted and try again.")
                        deld = dwd.find('\n')
                        continue
                    fdn = os.path.join(dd_use, bfn)  # Full Dest Name
                    # ensure destination directory exists and is accessible
                    if not os.path.isdir(dd_use):
                        print('Error: destination directory does not exist: {}'.format(dd_use))
                        ec += 1
                        self.gStat('Destination Directory {} Not Found'.format(dd_use),'black','red')
                        mb.showerror('Directory not found:',dd_use)
                        deld = dwd.find('\n')
                        continue
                    try:
                        ls = os.listdir(dd_use)
                    except Exception as e:
                        print('Error listing destination directory {}: {}'.format(dd_use, e))
                        ec += 1
                        self.gStat('Unable to read Destination Directory {}'.format(dd_use),'black','red')
                        mb.showerror('Directory not readable:', dd_use)
                        deld = dwd.find('\n')
                        continue
                    if bfn in ls:
                        try:
                            dflmt = os.path.getmtime(fdn)
                        except Exception:
                            dflmt = 0.0
                        v = ' updated on '
                        print('Destination file last modified timestame : {}'.format(dflmt))
                        its = int(dflmt)
                        print(dt.datetime.fromtimestamp(its).strftime('%Y-%m-%d %H:%M:%S'))
                    else:
                        print('File not yet in Destination directory.')
                        dflmt = 0.0
                        v = ' moved to '
                    # copy using shutil.copy2 to handle metadata and avoid manual open/write
                    if sflmt > dflmt:
                        # Try a full copy preserving metadata first; if the destination (e.g. gvfs/mtp)
                        # doesn't support metadata operations, fall back to a content-only copy.
                        try:
                            shutil.copy2(sf, fdn)
                        except Exception as e:
                            print('shutil.copy2 failed, falling back to content-only copy: {}'.format(e))
                            try:
                                with open(sf, 'rb') as src, open(fdn, 'wb') as dst:
                                    shutil.copyfileobj(src, dst)
                            except Exception as e2:
                                ec += 1
                                print('<< Error copying to Destination File>>\n{} -- {}'.format(e, e2))
                                self.gStat('Error copying to {}'.format(fdn), 'black', 'red')
                                deld = dwd.find('\n')
                                continue
                        m = '>> {}{}{}'.format(bfn, v, dd_use)
                        print(m)
                        if 'updated' in v:
                            uc += 1
                        else:
                            mc += 1
                        self.gStat(m,'black', 'green')
                    else:
                        m = '{} Up to date'.format(fdn)
                        print(m)
                        ac += 1
                        self.gStat(m,'black','Yellow')
                    deld = dwd.find('\n')
            m = 'Created: {}  Updated: {}  Not Old: {}  Errors: {}'.format(mc,uc,ac,ec)
            print(m)
            self.gStat(m,'white','blue')
       
    def _start_sync_thread(self, source_dir, dests, total_files):
        # Create progress window
        pw = Toplevel(self.master)
        pw.title('Sync Progress')
        Label(pw, text=f'Syncing {source_dir}').grid(row=0, column=0, padx=8, pady=8)
        progress_var = IntVar(value=0)
        pb = ttk.Progressbar(pw, maximum=total_files, variable=progress_var, length=600)
        pb.grid(row=1, column=0, padx=8, pady=4)
        status_label = Label(pw, text='Starting...')
        status_label.grid(row=2, column=0, padx=8, pady=4)
        cancel_event = threading.Event()
        def on_cancel():
            cancel_event.set()
            status_label.config(text='Cancelling...')
        Button(pw, text='Cancel', command=on_cancel).grid(row=3, column=0, padx=8, pady=6)
        pw.transient(self.master)
        pw.grab_set()

        def progress_cb_factory(pv, sl):
            # pv is IntVar, sl is Label
            def _cb(processed, total, filename):
                # schedule GUI update on main thread
                def gui_upd():
                    pv.set(processed)
                    sl.config(text=f"{processed}/{total}: {os.path.basename(filename)}")
                self.master.after(1, gui_upd)
            return _cb

        def worker():
            total_created = total_updated = total_skipped = total_errors = 0
            for dd in dests:
                if cancel_event.is_set():
                    break
                # reset progress for this destination
                self.master.after(1, lambda: progress_var.set(0))
                cb = progress_cb_factory(progress_var, status_label)
                try:
                    counts = self._sync_dir_to_dest(source_dir, dd, progress_callback=cb, total_files=total_files, stop_event=cancel_event)
                    total_created += counts.get('created',0)
                    total_updated += counts.get('updated',0)
                    total_skipped += counts.get('skipped',0)
                    total_errors += counts.get('errors',0)
                except Exception as e:
                    total_errors += 1
                    print('Error syncing {} -> {}: {}'.format(source_dir, dd, e))
            # finalize
            summary = f'Sync finished. Created:{total_created} Updated:{total_updated} Skipped:{total_skipped} Errors:{total_errors}'
            def finish():
                status_label.config(text=summary)
                Button(pw, text='Close', command=pw.destroy).grid(row=4, column=0, padx=8, pady=6)
                pw.grab_release()
            self.master.after(1, finish)
        th = threading.Thread(target=worker, daemon=True)
        th.start()

    def _sync_dir_to_dest(self, src_dir, dest_dir, progress_callback=None, total_files=None, stop_event=None):
        """Recursively sync src_dir into dest_dir. Returns counts dict.
        progress_callback(processed_count, total_files, current_file) optional.
        stop_event is threading.Event to allow cancellation.
        """
        counts = {'created': 0, 'updated': 0, 'skipped': 0, 'errors': 0}
        if not os.path.isdir(src_dir):
            raise FileNotFoundError(f"Source directory does not exist: {src_dir}")
        src_dir = os.path.normpath(src_dir)
        processed = 0
        for root, dirs, files in os.walk(src_dir):
            if stop_event and stop_event.is_set():
                break
            rel = os.path.relpath(root, src_dir)
            if rel == '.':
                rel = ''
            target_root = os.path.join(dest_dir, rel) if rel else dest_dir
            try:
                os.makedirs(target_root, exist_ok=True)
            except Exception as e:
                counts['errors'] += 1
                print(f"Could not create directory {target_root}: {e}")
                continue
            for fname in files:
                if stop_event and stop_event.is_set():
                    break
                src_f = os.path.join(root, fname)
                dest_f = os.path.join(target_root, fname)
                try:
                    s_mtime = os.path.getmtime(src_f)
                except Exception as e:
                    counts['errors'] += 1
                    print(f"Could not stat source file {src_f}: {e}")
                    continue
                if os.path.exists(dest_f):
                    try:
                        d_mtime = os.path.getmtime(dest_f)
                    except Exception:
                        d_mtime = 0
                else:
                    d_mtime = 0
                if s_mtime <= d_mtime:
                    counts['skipped'] += 1
                    processed += 1
                    if progress_callback:
                        progress_callback(processed, total_files, src_f)
                    continue
                # copy file (try copy2 then fallback)
                try:
                    shutil.copy2(src_f, dest_f)
                    if d_mtime == 0:
                        counts['created'] += 1
                    else:
                        counts['updated'] += 1
                except Exception as e:
                    # fallback to content-only
                    try:
                        with open(src_f, 'rb') as sfh, open(dest_f, 'wb') as dfh:
                            shutil.copyfileobj(sfh, dfh)
                    except Exception as e2:
                        counts['errors'] += 1
                        print(f"Error copying {src_f} -> {dest_f}: {e} -- {e2}")
                        processed += 1
                        if progress_callback:
                            progress_callback(processed, total_files, src_f)
                        continue
                    else:
                        if d_mtime == 0:
                            counts['created'] += 1
                        else:
                            counts['updated'] += 1
                processed += 1
                if progress_callback:
                    progress_callback(processed, total_files, src_f)
        return counts

root = Tk() 
cd = os.getcwd()
if cd.find('/') > -1:
    root.geometry('1000x520')  # linux Debian 10 - widened to show all buttons
    root.minsize(900,480)
else:
    root.geometry('900x420')  # Windows 10
    root.minsize(800,380)
app = win(root)
root.mainloop()

