#!/usr/bin/env python

import sys
import os
import subprocess
import re

try:
    import gtk
except ImportError:
    print 'This program requires pygtk'
    sys.exit()

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
        Sets up the GUI.
        Accepts an optional list of filenames to open
        '''
        self.build_ui()
        
        #values of the last used find, replace, and goto line entries
        self.last_find = ""
        self.last_replace = ""
        self.last_goto = ""
        
        #set up a clipboard
        self.clipboard = gtk.Clipboard()

        #set up a list to keep track of all the active tabs
        self.tabs = []

        #build a Tab object for the first page of the notebook
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
        self.window.connect('key-press-event',self.on_window_key_press_event)
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
        item = gtk.ImageMenuItem('_Goto Line')
        image = gtk.image_new_from_stock(gtk.STOCK_JUMP_TO,gtk.ICON_SIZE_MENU)
        item.set_image(image)
        key, mod = gtk.accelerator_parse('<Ctrl>G')
        item.add_accelerator('activate',accelgroup,key,mod,gtk.ACCEL_VISIBLE)
        item.connect('activate',self.on_menu_item_goto_activate)                
        menu.append(item)        
        menu_item.set_submenu(menu)
        menubar.add(menu_item)

        ### Tools Menu ###
        menu_item = gtk.MenuItem(label='_Tools',use_underline=True)
        menu = gtk.Menu()
        item = gtk.ImageMenuItem('_Run')
        image = gtk.image_new_from_stock(gtk.STOCK_EXECUTE,gtk.ICON_SIZE_MENU)
        item.set_image(image)
        key, mod = gtk.accelerator_parse('F5')
        item.add_accelerator('activate',accelgroup,key,mod,gtk.ACCEL_VISIBLE)        
        item.connect('activate',self.on_menu_item_run_activate)                
        menu.append(item)
        item = gtk.ImageMenuItem('Replace _Tabs with Spaces')
        image = gtk.image_new_from_stock(gtk.STOCK_GO_FORWARD,gtk.ICON_SIZE_MENU)
        item.set_image(image)
        item.connect('activate',self.on_menu_item_tabs_activate)
        menu.append(item)
        item = gtk.ImageMenuItem('Toggle Comments')
        image = gtk.image_new_from_stock(gtk.STOCK_REMOVE,gtk.ICON_SIZE_MENU)
        item.set_image(image)
        key, mod = gtk.accelerator_parse('<Ctrl>D')
        item.add_accelerator('activate',accelgroup,key,mod,gtk.ACCEL_VISIBLE)
        item.connect('activate',self.on_menu_item_comment_activate)
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

    def on_window_key_press_event(self,widget,data=None):
        '''
        check for <Ctrl>Tab or <Shift><Ctrl>Tab to switch tabs
        '''
        keyname = gtk.gdk.keyval_name(data.keyval)
        if data.state & gtk.gdk.CONTROL_MASK:
            if keyname == 'Tab':
                self.next_tab()
            if data.state & gtk.gdk.SHIFT_MASK:
                if keyname == 'ISO_Left_Tab':
                    self.prev_tab()

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
        tab = self.current_tab()
        textview = tab.get_textview()
        textbuffer = textview.get_buffer()
        dialog = gtk.Dialog(
                    title = 'Find',
                    parent = self.window,
                    flags = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                    buttons = ('Find',gtk.RESPONSE_ACCEPT))
        dialog.set_property('resizable',False)
        entry = gtk.Entry()
        entry.set_text(self.last_find)
        dialog.add_action_widget(entry,gtk.RESPONSE_ACCEPT)
        box = dialog.get_action_area()
        box.reorder_child(entry,0)
        entry.show()
        done = False
        while not done:
            response = dialog.run()
            search = ""
            if response == gtk.RESPONSE_ACCEPT:
                search = entry.get_text()
                self.last_find = search
                bounds = textbuffer.get_selection_bounds()
                if bounds:
                    cur_iter = bounds[1]
                else:
                    cur_iter = textbuffer.get_iter_at_mark(textbuffer.get_insert())
                found = cur_iter.forward_search(search,flags=0)
                if found:
                   match_start,match_end = found
                   textbuffer.select_range(match_start,match_end)
                   textview.scroll_to_iter(match_start,0.1)
                else:
                    #loop around to beginning, stopping at cursor position
                    start_iter = textbuffer.get_start_iter()
                    found = start_iter.forward_search(search,flags=0,limit=cur_iter)
                    if found:
                       match_start,match_end = found
                       textbuffer.select_range(match_start,match_end)
                       textview.scroll_to_iter(match_start,0.1)
            else:
                done = True
                dialog.destroy()  

    def on_menu_item_replace_activate(self,widget,data=None):
        tab = self.current_tab()
        textview = tab.get_textview()
        textbuffer = textview.get_buffer()
        RESPONSE_FIND = 1
        RESPONSE_REPLACE = 2
        dialog = gtk.Dialog(
                    title = 'Find & Replace',
                    parent = self.window,
                    flags = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                    buttons = ('Find',RESPONSE_FIND,
                               'Replace',RESPONSE_REPLACE))
        dialog.set_property('resizable',False)
        find_label = gtk.Label('Find')
        find_entry = gtk.Entry()
        find_entry.set_text(self.last_find)
        replace_label = gtk.Label('Replace')
        replace_entry = gtk.Entry()
        replace_entry.set_text(self.last_replace)
        table = gtk.Table(2,2)
        table.attach(find_label,0,1,0,1)
        table.attach(find_entry,1,2,0,1)
        table.attach(replace_label,0,1,1,2)
        table.attach(replace_entry,1,2,1,2)
        table.set_col_spacing(0,10)
        box = dialog.get_content_area()
        box.pack_start(table,fill=False,expand=False,padding=0)
        box.show_all()
        done = False
        while not done:
            response = dialog.run()
            find = ""
            replace = ""
            if response == RESPONSE_FIND or response == RESPONSE_REPLACE:
                find = find_entry.get_text()
                replace = replace_entry.get_text()
                self.last_find = find
                self.last_replace = replace
                bounds = textbuffer.get_selection_bounds()
                if response == RESPONSE_FIND and bounds:
                    cur_iter = bounds[1]
                else:
                    cur_iter = textbuffer.get_iter_at_mark(textbuffer.get_insert())
                found = cur_iter.forward_search(find,flags=0)
                if found:
                   match_start,match_end = found
                   textbuffer.select_range(match_start,match_end)
                   textview.scroll_to_iter(match_start,0.1)
                   if response == RESPONSE_REPLACE:
                       textbuffer.insert(match_start,replace)
                       textbuffer.delete_selection(1,1)
                else:
                    #loop around to beginning, stopping at cursor position
                    start_iter = textbuffer.get_start_iter()
                    found = start_iter.forward_search(find,flags=0,limit=cur_iter)
                    if found:
                       match_start,match_end = found
                       textbuffer.select_range(match_start,match_end)
                       textview.scroll_to_iter(match_start,0.1)
                       if response == RESPONSE_REPLACE:
                           textbuffer.insert(match_start,replace)
                           textbuffer.delete_selection(1,1)
                if response == RESPONSE_REPLACE:
                    bounds = textbuffer.get_selection_bounds()
                    if bounds:
                        cur_iter = bounds[1]
                    else:
                        cur_iter = textbuffer.get_iter_at_mark(textbuffer.get_insert())
                    found = cur_iter.forward_search(find,flags=0)
                    if found:
                       match_start,match_end = found
                       textbuffer.select_range(match_start,match_end)
                       textview.scroll_to_iter(match_start,0.1)
                    else:
                        #loop around to beginning, stopping at cursor position
                        start_iter = textbuffer.get_start_iter()
                        found = start_iter.forward_search(find,flags=0,limit=cur_iter)
                        if found:
                           match_start,match_end = found
                           textbuffer.select_range(match_start,match_end)
                           textview.scroll_to_iter(match_start,0.1)
            else:
                done = True
                dialog.destroy()

    def on_menu_item_goto_activate(self,widget,data=None):
        tab = self.current_tab()
        textview = tab.get_textview()
        textbuffer = textview.get_buffer()
        dialog = gtk.Dialog(
                    title = 'Goto Line',
                    parent= self.window,
                    flags = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                    buttons = ('Goto',gtk.RESPONSE_ACCEPT))
        dialog.set_property('resizable',False)
        entry = gtk.Entry()
        entry.set_text(self.last_goto)
        dialog.add_action_widget(entry,gtk.RESPONSE_ACCEPT)
        box = dialog.get_action_area()
        box.reorder_child(entry,0)
        entry.show()
        response = dialog.run()
        line = 0
        if response == gtk.RESPONSE_ACCEPT:
            line = entry.get_text()
            self.last_goto = line
        dialog.destroy()
        if line:
            try:
                line_num = int(line)
                line_num = line_num - 1
            except:
                line_num = ''
            if line_num is not '' and line_num >= 0:
                try:
                    textiter = textbuffer.get_iter_at_line(line_num)
                    textbuffer.place_cursor(textiter)
                    textview.scroll_to_iter(textiter,0.1)
                except OverflowError:
                    pass

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
    
    def on_menu_item_tabs_activate(self,widget,data=None):
        if self.tabs:
            tab = self.current_tab()
            textview = tab.get_textview()
            textbuffer = textview.get_buffer()
            textview.set_sensitive(False)
            start = textbuffer.get_start_iter()
            end = textbuffer.get_end_iter()
            text = textbuffer.get_text(start,end,True)
            text = re.sub('\t','    ',text)
            textbuffer.set_text(text)
            textview.set_sensitive(True)
   
    def on_menu_item_comment_activate(self,widget,data=None):
        if self.tabs:
            tab = self.current_tab()
            tab.comment()
         
    ### notebook signal handlers ###

    def on_notebook_switch_page(self,widget,data=None,new_page_num=None):
        if self.tabs:
            tab = self.tabs[new_page_num]
            tab.update_statusbar()

    ###########################

    def quit(self):
        changes = 0
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
        tab = Tab(self.notebook,self.statusbar)
        self.tabs.append(tab)
        self.notebook.set_current_page(len(self.tabs)-1)
        #reset the flag to indicate that we no longer
        #have just the original "New Document" tab
        self.only_first_tab = 0
    
    def next_tab(self):
        '''
        advance to the next tab
        loops around to first tab if at the end
        '''
        if self.tabs:
            cur_tab = self.current_page()
            num_tabs = len(self.tabs)-1
            if num_tabs > 0:
                if cur_tab == num_tabs:
                    self.notebook.set_current_page(0)
                else:
                    self.notebook.set_current_page(cur_tab+1)
                self.current_tab().focus()
                                
    def prev_tab(self):
        '''
        move back to the previous tab
        loops around to last tab if at the beginning
        '''
        if self.tabs:
            cur_tab = self.current_page()
            num_tabs = len(self.tabs)-1
            if num_tabs > 0:
                if cur_tab == 0:
                    self.notebook.set_current_page(num_tabs)
                else:
                    self.notebook.set_current_page(cur_tab-1)
                self.current_tab().focus()
   
    def load_file(self,filename):
        try:
            f = open(filename,'r')
            text = f.read()
            f.close()
            tab = self.current_tab()
            textview = tab.get_textview()
            textbuffer = textview.get_buffer()
            textview.set_sensitive(False)
            textbuffer.set_text(text)
            start = textbuffer.get_start_iter()
            textbuffer.place_cursor(start)
            textbuffer.set_modified(False)
            textview.set_sensitive(True)
            tab.set_filename(filename)
            tab.update_statusbar()
        except IOError as e:
            print("Couldn't open file %s" % filename)

    def save_file(self,filename):
        if filename:
            tab = self.current_tab()
            textview = tab.get_textview()
            textbuffer = textview.get_buffer()
            start = textbuffer.get_start_iter()
            end = textbuffer.get_end_iter()
            text = textbuffer.get_text(start,end)
            try:
                f = open(filename,'w')
                f.write(text)
                f.close()
                textbuffer.set_modified(False)
                tab.set_filename(filename)
                tab.update_statusbar()
            except IOError as e:
                print("Error saving file %s" % filename)

    def close_tab(self):
        if self.tabs:
            page = self.current_page()
            tab = self.current_tab()
            quit = True
            if tab.has_unsaved_changes():
                if not self.ok_to_close_tab():
                    quit = False
            if quit:
                self.notebook.remove_page(page)
                self.tabs.remove(tab)                

    def ok_to_close_tab(self):
        dialog = gtk.MessageDialog(parent=self.window,
                                  flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                                  type=gtk.MESSAGE_QUESTION,
                                  buttons=gtk.BUTTONS_OK_CANCEL,
                                  message_format="Tab has unsaved changes, are you sure you want to close it?")
        dialog_response = dialog.run()
        ok_to_quit = False
        if dialog_response == gtk.RESPONSE_OK:
            ok_to_quit = True
        dialog.destroy()
        return ok_to_quit

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
        style_scheme_manager = gtksourceview2.style_scheme_manager_get_default()
        cur_path = os.path.abspath(sys.path[0])
        styles_path = os.path.join(cur_path,'styles')
        style_scheme_manager.prepend_search_path(styles_path)
        scheme = style_scheme_manager.get_scheme('coder')
            
    def __init__(self,notebook,statusbar):
        self.notebook = notebook
        self.statusbar = statusbar
        self.filename = ""
        self.changed = 0
        self.line = 0
        self.col = 0
        self.create_widgets()
        self.notebook.append_page(self.window,self.label)
        self.window.show()
        self.textview.show()
        self.focus()
    
    def create_widgets(self):
        'Creates the Scrolled Window, Text View, and Label'
        self.window = gtk.ScrolledWindow()
        self.window.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
        if SOURCE_VIEW:
            self.textbuffer = gtksourceview2.Buffer()
            self.textbuffer.set_style_scheme(Tab.scheme)
            self.textview = gtksourceview2.View(self.textbuffer)
        else:
            self.textbuffer = gtk.TextBuffer()
            self.textview = gtk.TextView(self.textbuffer)
        self.textbuffer.create_tag('font',font='Monospace 10')
        self.textbuffer.apply_tag_by_name('font',self.textbuffer.get_start_iter(),self.textbuffer.get_end_iter())
        self.textview.connect('event',self.textview_event)
        self.textview.connect('event-after',self.textview_event_after)
        self.textbuffer.connect('modified-changed',self.buffer_modified_changed)
        self.textbuffer.connect('changed',self.buffer_changed)
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

    def textview_event(self,widget,event,data=None):
        '''
        Intercepts tab keypresses and redirects to the indent function
        Intercepts return keypresses and redirects to the autoindent function
        '''
        if event.type == gtk.gdk.KEY_PRESS:
            keyname = gtk.gdk.keyval_name(event.keyval)
            if keyname == 'Tab':
                self.indent()
                return True
            elif keyname == 'ISO_Left_Tab' and (event.state & gtk.gdk.SHIFT_MASK):
                self.indent(reverse=True)
                return True
            elif keyname == 'Return':
                self.autoindent()
                return True

    def indent(self,reverse=False):
        '''
        Replaces tabs with 4 spaces.
        Set reverse to True to unindent.
        If multiple lines are selected the whole block will be indented/unindented.
        '''
        tab = '    ' # 4 spaces
        bounds = self.textbuffer.get_selection_bounds()
        if bounds:
            # a block is selected, indent/unindent the entire line(s)
            start,end = bounds
            start_line = start.get_line()
            end_line = end.get_line()
            for line in range(start_line,end_line+1):
                textiter = self.textbuffer.get_iter_at_line_offset(line,0)
                if reverse:
                    if textiter.get_chars_in_line() >= 5:
                        textiter_end = self.textbuffer.get_iter_at_line_offset(line,4)
                        text = self.textbuffer.get_text(textiter,textiter_end,True)
                        if text == tab:
                            self.textbuffer.delete(textiter,textiter_end)
                else:
                    self.textbuffer.insert(textiter,tab)
        else:
            # there's no selection, just replace the tab with 4 spaces
            # if unindenting, check if there are 4 spaces before the cursor and if so, delete them
            if reverse:
                textiter_end = self.textbuffer.get_iter_at_mark(self.textbuffer.get_insert())
                line = textiter_end.get_line()
                col = textiter_end.get_line_offset() - 4
                if col >= 0:
                    textiter = self.textbuffer.get_iter_at_line_offset(line,col)
                    text = self.textbuffer.get_text(textiter,textiter_end,True)
                    if text == tab:
                        self.textbuffer.delete(textiter,textiter_end)
            else:
                self.textbuffer.insert_at_cursor(tab)

    def autoindent(self):
        '''
        Auto indents the next line to line up with the previous one.
        If the previous line ends in ':', then an extra tab (4 spaces) is added.
        '''
        self.textbuffer.insert_at_cursor('\n')
        textiter = self.textbuffer.get_iter_at_mark(self.textbuffer.get_insert())
        line = textiter.get_line()
        if line > 0:
            textiter = self.textbuffer.get_iter_at_line_offset(line-1,0)
            textiter_end = textiter.copy()
            if textiter_end.forward_to_line_end():
                text = self.textbuffer.get_text(textiter,textiter_end,True)
                spaces = 0
                for c in text:
                    if c == ' ':
                        spaces = spaces + 1
                    else:
                        break
                if text[-1] == ':':
                    spaces = spaces + 4
                if spaces > 0:
                    text = ' ' * spaces
                    self.textbuffer.insert_at_cursor(text)

    def comment(self):
        '''
        Set the first character of the current/highlighted lines to '#'.
        If it already is set then remove it.
        '''
        comment = '#'
        bounds = self.textbuffer.get_selection_bounds()
        start_line = None
        end_line = None
        if bounds:
            # a block is selected, comment all of the lines
            start,end = bounds
            start_line = start.get_line()
            end_line = end.get_line()
        else:
            textiter = self.textbuffer.get_iter_at_mark(self.textbuffer.get_insert())
            start_line = textiter.get_line()
            end_line = start_line
        for line in range(start_line,end_line+1):
            textiter_start = self.textbuffer.get_iter_at_line_offset(line,0)
            if textiter_start.get_chars_in_line() >= 2:
                textiter_end = self.textbuffer.get_iter_at_line_offset(line,1)
                text = self.textbuffer.get_text(textiter_start,textiter_end,True)
                if text == comment:
                    self.textbuffer.delete(textiter_start,textiter_end)
                else:
                    self.textbuffer.insert(textiter_start,comment)
            else:
                self.textbuffer.insert(textiter_start,comment)

    def textview_event_after(self,widget,event,data=None):
        pos = self.textbuffer.get_property('cursor-position')
        textiter = self.textbuffer.get_iter_at_offset(pos)
        line = textiter.get_line()
        col = textiter.get_line_offset()
        changed = False
        if self.line != line:
            self.line = line
            changed = True
        if self.col != col:
            self.col = col
            changed = True
        if changed:
            self.update_statusbar()

    def update_statusbar(self):
        status = '%s       Line: %s  Col: %s' % (self.filename,self.line+1,self.col+1)
        context_id = self.statusbar.get_context_id("status")
        self.statusbar.pop(context_id)
        self.statusbar.push(context_id,status)        

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
    
    def buffer_changed(self,widget):
        self.textbuffer.apply_tag_by_name('font',self.textbuffer.get_start_iter(),self.textbuffer.get_end_iter())

    def has_unsaved_changes(self):
        return self.changed

    def focus(self):
        # this should set focus to the textview but doesn't always work
        self.textview.grab_focus()

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
        

