#!/usr/bin/env python

import sys
import os
import gtk
import subprocess

# try to import gtksourceview2
# if it doesn't exist then we'll just use a normal text view
try:
    import gtksourceview2
    SOURCE_VIEW = 1
except ImportError:
    SOURCE_VIEW = 0


class TextEditor(object):
    '''
    The main GUI of the application.
    A window with a tabbed notebook interface
    '''

    def __init__(self,filenames=[]):
        '''
        Loads the Glade file and sets up the GUI.
        Accepts an optional list of filenames to open
        '''

        #builder = gtk.Builder()
        #builder.add_from_file("coder.glade")
        
        #gtk objects from glade
        #self.window_old = builder.get_object("window")
        #self.window_old.hide()
        #self.notebook_old = builder.get_object("notebook")
        #self.notebook_old.hide()
        #self.vbox_old = builder.get_object("vbox")
        #self.vbox_old.hide()
        #self.window.remove(self.vbox_old)
        #self.statusbar_old = builder.get_object("statusbar")
        #self.statusbar_old.hide()

        #scrolledwindow = builder.get_object("scrolledwindow")
        #textview = builder.get_object("textview")
        #label = builder.get_object("notebook_label")
        
        #hide the tab widgets, we'll create our own
        #scrolledwindow.hide()
        #textview.hide()
        #label.hide()
        
        self.build_ui()
        
        #remove the notebook tab that was created by glade
        self.notebook.remove_page(0)

        #link the signal handlers
        #builder.connect_signals(self)


        #set up a clipboard
        self.clipboard = gtk.Clipboard()

        #set up a list to keep track of all the active tabs
        self.tabs = []

        #build a Tab object for the first page of the notebook
        #tab = Tab(self.notebook,scrolledwindow,textview,label)
        #self.tabs.append(tab)
        self.new_tab()

        #load files from the command line if there were any
        if filenames:
            self.only_first_tab = 0
            self.load_file(filenames[0])
            filenames = filenames[1:]
            # if there was more than 1 filename then
            # create tabs for each one and load the files
            for f in filenames:
                self.new_tab()
                self.load_file(f)
        else:
            #open works differently if there's only the original "New Document" tab
            self.only_first_tab = 1

    def build_ui(self):
        ### Window ###
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_title('Coder')
        self.window.set_default_size(800,1000)
        self.window.connect('delete-event',self.on_window_delete_event)
        self.window.connect('destroy',self.on_window_destroy)
        accelgroup = gtk.AccelGroup()
        self.window.add_accel_group(accelgroup)

        ### Main Container ###
        vbox = gtk.VBox()
        self.window.add(vbox)
        vbox.show()

        ### Menus ###    
        menubar = gtk.MenuBar()

        ### File Menu ###
        menu_item = gtk.MenuItem(label='_File',use_underline=True)
        menu = gtk.Menu()
        item = gtk.ImageMenuItem(gtk.STOCK_NEW,accelgroup)
        item.connect('activate',self.on_menu_item_new_activate)                
        menu.append(item)
        item = gtk.ImageMenuItem(gtk.STOCK_OPEN,accelgroup)
        item.connect('activate',self.on_menu_item_open_activate)       
        menu.append(item)
        item = gtk.ImageMenuItem(gtk.STOCK_SAVE,accelgroup)
        item.connect('activate',self.on_menu_item_save_activate)       
        menu.append(item)
        item = gtk.ImageMenuItem(gtk.STOCK_SAVE_AS,accelgroup)
        item.connect('activate',self.on_menu_item_save_as_activate)       
        menu.append(item)
        item = gtk.ImageMenuItem(gtk.STOCK_CLOSE,accelgroup)
        item.connect('activate',self.on_menu_item_close_activate)       
        menu.append(item)
        item = gtk.SeparatorMenuItem()
        menu.append(item)
        item = gtk.ImageMenuItem(gtk.STOCK_QUIT,accelgroup)
        item.connect('activate',self.on_menu_item_quit_activate)       
        menu.append(item)
        menu_item.set_submenu(menu)
        menubar.add(menu_item)

        ### Edit Menu ###
        menu_item = gtk.MenuItem(label='_Edit',use_underline=True)
        menu = gtk.Menu()
        item = gtk.ImageMenuItem(gtk.STOCK_CUT,accelgroup)
        item.connect('activate',self.on_menu_item_cut_activate)       
        menu.append(item)
        item = gtk.ImageMenuItem(gtk.STOCK_COPY,accelgroup)
        item.connect('activate',self.on_menu_item_copy_activate)       
        menu.append(item)
        item = gtk.ImageMenuItem(gtk.STOCK_PASTE,accelgroup)
        item.connect('activate',self.on_menu_item_paste_activate)       
        menu.append(item)
        menu_item.set_submenu(menu)
        menubar.add(menu_item)

	    ### Search Menu ###
        menu_item = gtk.MenuItem(label='_Search',use_underline=True)
        menu = gtk.Menu()
        item = gtk.ImageMenuItem(gtk.STOCK_FIND,accelgroup)
        item.connect('activate',self.on_menu_item_find_activate)                
        menu.append(item)
        item = gtk.ImageMenuItem(gtk.STOCK_FIND_AND_REPLACE,accelgroup)
        item.connect('activate',self.on_menu_item_replace_activate)                
        menu.append(item)
        item = gtk.MenuItem(label='_Goto Line',use_underline=True)
        key, mod = gtk.accelerator_parse("<Ctrl>G")
        item.add_accelerator("activate",accelgroup,key,mod,gtk.ACCEL_VISIBLE)        
        item.connect('activate',self.on_menu_item_goto_activate)                
        menu.append(item)        
        menu_item.set_submenu(menu)
        menubar.add(menu_item)

    	### Tools Menu ###
        menu_item = gtk.MenuItem(label='_Tools',use_underline=True)
        menu = gtk.Menu()
        item = gtk.ImageMenuItem(gtk.STOCK_EXECUTE,accelgroup)
        item.connect('activate',self.on_menu_item_run_activate)                
        menu.append(item)
        menu_item.set_submenu(menu)
        menubar.add(menu_item)

        menubar.show_all()
        vbox.pack_start(menubar,expand=False,fill=True,padding=0)

        ### Notebook ###
        self.notebook = gtk.Notebook()
        self.notebook.connect('switch-page',self.on_notebook_switch_page)        
        vbox.pack_start(self.notebook,expand=True,fill=True,padding=0)
        self.notebook.show()

        ### Status Bar ###
        self.statusbar = gtk.Statusbar()
        vbox.pack_start(self.statusbar,expand=False,fill=True,padding=0)
        self.statusbar.set_spacing(2)
        self.statusbar.show()

        self.window.show()
        
    ### window signal handlers ###
    
    def on_window_delete_event(self,widget,data=None):
        self.quit()
        #return True so the signal doesn't propagate up to gtk.Object.destroy
        #and kill our window even if there are unsaved changes
        return True

    def on_window_destroy(self,widget,data=None):
        pass

    ### file menu handlers ###

    def on_menu_item_new_activate(self,widget,data=None):
        self.new_tab()
    
    def on_menu_item_open_activate(self,widget,data=None):
        file_chooser = gtk.FileChooserDialog(
                        title = 'Open',
                        action = gtk.FILE_CHOOSER_ACTION_OPEN,
                        buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                                   gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        response = file_chooser.run()
        if response == gtk.RESPONSE_ACCEPT:
            #if there's only the original "New Document" tab
            #then don't create a new tab, just replace the original
            if not self.only_first_tab:
                self.new_tab()
            #if there are no open tabs at all then create one first
            if not self.tabs:
                self.new_tab()
            filename = file_chooser.get_filename()
            self.load_file(filename)
            #reset the flag to indicate that we no longer
            #have just the original "New Document" tab
            self.only_first_tab = 0
        file_chooser.destroy()

    def on_menu_item_save_activate(self,widget,data=None):
        if self.tabs:
            tab = self.current_tab()
            filename = tab.get_filename()
            if filename:
                self.save_file(filename)
            else:
                self.on_menu_item_save_as_activate(widget,data)

    def on_menu_item_save_as_activate(self,widget,data=None):
        if self.tabs:
            file_chooser = gtk.FileChooserDialog(
                            title = 'Save as',
                            action = gtk.FILE_CHOOSER_ACTION_SAVE,
                            buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                                    gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
            response = file_chooser.run()
            if response == gtk.RESPONSE_ACCEPT:
                filename = file_chooser.get_filename()
                ok_to_save = True
                if os.path.exists(filename):
                    current_filename = self.current_tab().get_filename()
                    if current_filename != filename:
                        if not self.ok_to_overwrite_file(filename):
                            ok_to_save = False
                if ok_to_save:
                    self.save_file(filename)
            file_chooser.destroy()

    def on_menu_item_close_activate(self,widget,data=None):
        self.close_tab()

    def on_menu_item_quit_activate(self,widget,data=None):
        self.quit()

    ### edit menu signal handlers ###

    def on_menu_item_cut_activate(self,widget,data=None):
        if self.tabs:
            tab = self.current_tab()
            textview = tab.get_textview()
            textbuffer = textview.get_buffer()
            textbuffer.cut_clipboard(self.clipboard,textview.get_editable())

    def on_menu_item_copy_activate(self,widget,data=None):
        if self.tabs:
            tab = self.current_tab()
            textview = tab.get_textview()
            textbuffer = textview.get_buffer()
            textbuffer.copy_clipboard(self.clipboard)

    def on_menu_item_paste_activate(self,widget,data=None):
        if self.tabs:
            tab = self.current_tab()
            textview = tab.get_textview()
            textbuffer = textview.get_buffer()
            textbuffer.paste_clipboard(self.clipboard,None,textview.get_editable())

    ### search menu signal handlers ###

    def on_menu_item_find_activate(self,widget,data=None):
        print('on_menu_item_find_activate')
        
        tab = self.current_tab()
        textview = tab.get_textview()
        textbuffer = textview.get_buffer()
       
        search_str =  'blah'
        start_iter =  textbuffer.get_start_iter() 
        #match_start = textbuffer.get_start_iter() 
        #match_end =   textbuffer.get_end_iter() 
        found =       start_iter.forward_search(search_str,0, None) 
        if found:
           match_start,match_end = found
           textbuffer.select_range(match_start,match_end)

        
    def on_menu_item_replace_activate(self,widget,data=None):
        print('on_menu_item_replace_activate')

    def on_menu_item_goto_activate(self,widget,data=None):
        print('on_menu_item_goto_activate')
        
    ### tools menu signal handlers ###

    def on_menu_item_run_activate(self,widget,data=None):
        if self.tabs:
            tab = self.current_tab()
            filename = tab.get_filename()
            if filename:
                (basename,ext) = os.path.splitext(filename)
                if os.path.exists(filename) and ext == '.py':
                    try:
                        command = 'python ' + filename
                        subprocess.Popen('python ' + filename,shell=True)
                    except OSError as e:
                        print e
    
    ### notebook signal handlers ###

    def on_notebook_switch_page(self,widget,data=None,new_page_num=None):
        filename = ""
        if self.tabs:
            tab = self.tabs[new_page_num]
            filename = tab.get_filename()
        context_id = self.statusbar.get_context_id("filename")
        self.statusbar.push(context_id,filename)

        
    ###########################

    def quit(self):
        changes = 0
        quit = 0
        for tab in self.tabs:
            if tab.has_unsaved_changes():
                changes = 1
                break
        if changes:
            if self.ok_to_quit():
                gtk.main_quit()
            else:
                return False
        else:
            gtk.main_quit()

    def ok_to_quit(self):
        dialog = gtk.MessageDialog(parent=self.window,
                                  flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                                  type=gtk.MESSAGE_QUESTION,
                                  buttons=gtk.BUTTONS_OK_CANCEL,
                                  message_format="There are unsaved changes, are you sure you want to quit?")
        dialog_response = dialog.run()
        ok_to_quit = False
        if dialog_response == gtk.RESPONSE_OK:
            ok_to_quit = True
        dialog.destroy()
        return ok_to_quit

    def current_page(self):
        return self.notebook.get_current_page()

    def current_tab(self):
        if self.tabs:
            return self.tabs[self.current_page()]
        else:
            return -1

    def new_tab(self):
        tab = Tab(self.notebook)
        self.tabs.append(tab)
        self.notebook.set_current_page(len(self.tabs)-1)
        #reset the flag to indicate that we no longer
        #have just the original "New Document" tab
        self.only_first_tab = 0
    
    def load_file(self,filename):
        try:
            f = open(filename,'r')
            text = f.read()
            f.close()
            
            tab = self.current_tab()
            textview = tab.get_textview()
            textbuffer = textview.get_buffer()
            
            #disable the text view while loading the buffer
            textview.set_sensitive(False)
            
            #store the file's contents in the buffer
            textbuffer.set_text(text)
            textbuffer.set_modified(False)
            
            #turn the text view back on
            textview.set_sensitive(True)
          
            #update the filename and label of the tab
            tab.set_filename(filename)
            
            #update the status bar
            context_id = self.statusbar.get_context_id("filename")
            self.statusbar.push(context_id,filename)

            print("Loaded %s" % filename)
        except IOError as e:
            print("Couldn't open file %s" % filename)

    def save_file(self,filename):
        if filename:
            tab = self.current_tab()
            textview = tab.get_textview()
            textbuffer = textview.get_buffer()
            start = textbuffer.get_start_iter()
            end = textbuffer.get_end_iter()

            # get the full text in the buffer
            text = textbuffer.get_text(start,end)

            try:
                f = open(filename,'w')
                f.write(text)
                f.close()

                # reset the modified flag
                textbuffer.set_modified(False)

                #update the filename and label of the tab
                tab.set_filename(filename)

                #update the status bar
                context_id = self.statusbar.get_context_id("filename")
                self.statusbar.push(context_id,filename)

                print("Saved %s" % filename)
            except IOError as e:
                print("Error saving file %s" % filename)

    def close_tab(self):
        if self.tabs:
            self.notebook.remove_page(self.current_page())
            self.tabs.remove(self.current_tab())

    def ok_to_overwrite_file(self,filename):
        dialog = gtk.MessageDialog(parent=self.window,
                                  flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                                  type=gtk.MESSAGE_QUESTION,
                                  buttons=gtk.BUTTONS_OK_CANCEL,
                                  message_format="File exists. Overwrite?")
        dialog_response = dialog.run()
        ok_to_overwrite = False
        if dialog_response == gtk.RESPONSE_OK:
            ok_to_overwrite = True
        dialog.destroy()
        return ok_to_overwrite


class Tab(object):
    '''
    Manages the Scrolled Window, Text View, Text Buffer, Label, and File
    that make up a tab in the Text Editor.
    '''

    if SOURCE_VIEW:
        source_language_manager = gtksourceview2.language_manager_get_default()
        langs = {'py':'python','glade':'xml','pl':'perl'}
    
    def __init__(self,notebook,window=None,textview=None,label=None):
        '''
        The first tab is built by Glade, we just need to store the widgets.
        Subsequent tabs are built dynamically, only the notebook
        argument should be used for those.
        '''
        #TODO: we should always be creating the widgets dynamically now
        # the window, textview, and label params should be removed

        self.notebook = notebook
        self.filename = ""
        self.changed = 0

        if window is None:
            self.create_widgets()
            self.notebook.append_page(self.window,self.label)
        else:
            # widgets were already built by glade
            self.window = window
            self.textview = textview
            self.label = label
 
        self.window.show()
        self.textview.show()
    
    def create_widgets(self):
        'Creates the Scrolled Window, Text View, and Label'
        self.window = gtk.ScrolledWindow()
        self.window.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
        if SOURCE_VIEW:
            self.textbuffer = gtksourceview2.Buffer()
            self.textview = gtksourceview2.View(self.textbuffer)
        else:
            self.textbuffer = gtk.TextBuffer()
            self.textview = gtk.TextView(self.textbuffer)
        self.textbuffer.connect('modified-changed',self.buffer_modified_changed)        
        self.window.add(self.textview)
        self.label = gtk.Label("New Document")        
    
    def get_window(self):
        return self.window

    def get_textview(self):
        return self.textview

    def get_label(self):
        return self.label

    def get_filename(self):
        return self.filename

    def set_filename(self,filename):
        '''
        Set the filename, update the label,
        and set the syntax hightlighting
        '''
        self.filename = filename
        self.label.set_text(os.path.basename(filename))
        self.notebook.set_tab_label(self.window,self.label)
        self.update_source_buffer(filename)

    def update_source_buffer(self,filename):
        'Set the syntax highlighting based on filename'
        if not SOURCE_VIEW: return
        (basename,ext) = os.path.splitext(filename)
        #strip off the "." from the extension
        ext = ext[1:]
        #get the lang_id from the extension, ex: 'py' -> 'python'
        try:
            lang_id = Tab.langs[ext]
        except KeyError:
            #if the extension isn't in the list of langs 
            #then just use the extension, ex: 'c'
            #if lang_id isn't a valid id, the language manager
            #just ignores it
            lang_id = ext
        language = Tab.source_language_manager.get_language(lang_id)
        self.textbuffer.set_language(language)

    def buffer_modified_changed(self,widget):
        if self.changed:
            self.changed = 0
            if self.filename:
                text = os.path.basename(self.filename)
            else:
                text = "New Document"
            self.label.set_text(text)
        else:
            self.changed = 1
            if self.filename:
                text = os.path.basename(self.filename) + " *"
            else:
                text = "New Document *"
            self.label.set_text(text)            
    
    def has_unsaved_changes(self):
        return self.changed

def main(filenames=[]):
    '''
    Creates the Text Editor object and starts GTK.
    Accepts an optional list of filenames to pass to the Text Editor
    '''
    editor = TextEditor(filenames)
    editor.window.show()
    gtk.main()

if __name__ == "__main__":
    filenames = sys.argv[1:]
    main(filenames)
        

