'''
Copyright 2010 John Murphy
This file is part of Coder.

Coder is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Coder is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Coder.  If not, see <http://www.gnu.org/licenses/>.
'''

import sys
import os
import subprocess
import re
import gtk
import gtksourceview2

from tab import Tab
from coder import MAIN_PATH
import menus

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
        try:
            icon_filename = os.path.join(MAIN_PATH,'data/icon.png')
            self.window.set_icon_from_file(icon_filename)
        except:
            print "Error: Couldn't load icon"
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
        menubar = menus.build_main_menu(self,accelgroup)
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
                return True
            if data.state & gtk.gdk.SHIFT_MASK:
                if keyname == 'ISO_Left_Tab':
                    self.prev_tab()
                    return True

    def on_notebook_switch_page(self,widget,data=None,new_page_num=None):
        if self.tabs:
            tab = self.tabs[new_page_num]
            tab.update_statusbar()

    def file_open(self):
        file_chooser = gtk.FileChooserDialog(
                        title = 'Open',
                        action = gtk.FILE_CHOOSER_ACTION_OPEN,
                        buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                                   gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        if self.tabs:
            tab = self.current_tab()
            file_chooser.set_current_folder(tab.get_current_folder())
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

    def file_save(self):
        if self.tabs:
            tab = self.current_tab()
            filename = tab.get_filename()
            if filename:
                self.save_file(filename)
            else:
                self.file_save_as()

    def file_save_as(self):
        if self.tabs:
            file_chooser = gtk.FileChooserDialog(
                            title = 'Save as',
                            action = gtk.FILE_CHOOSER_ACTION_SAVE,
                            buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                                    gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
            tab = self.current_tab()
            file_chooser.set_current_folder(tab.get_current_folder())
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

    ### edit menu signal handlers ###

    def cut(self):
        if self.tabs:
            tab = self.current_tab()
            textview = tab.get_textview()
            textbuffer = textview.get_buffer()
            textbuffer.cut_clipboard(self.clipboard,textview.get_editable())

    def copy(self):
        if self.tabs:
            tab = self.current_tab()
            textview = tab.get_textview()
            textbuffer = textview.get_buffer()
            textbuffer.copy_clipboard(self.clipboard)

    def paste(self):
        if self.tabs:
            tab = self.current_tab()
            textview = tab.get_textview()
            textbuffer = textview.get_buffer()
            textbuffer.paste_clipboard(self.clipboard,None,textview.get_editable())

    ### search menu signal handlers ###

    def find(self):
        tab = self.current_tab()
        textview = tab.get_textview()
        textbuffer = textview.get_buffer()
        dialog = gtk.Dialog(
                    title = 'Find',
                    parent = self.window,
                    flags = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                    buttons = ('Find',gtk.RESPONSE_ACCEPT))
        dialog.set_property('resizable',False)
        label = gtk.Label('Find')
        entry = gtk.Entry()
        entry.set_text(self.last_find)
        # we want the text entry to emit the response but we don't want it
        # in the action area (where the buttons are)
        dialog.add_action_widget(entry,gtk.RESPONSE_ACCEPT)
        action_area = dialog.get_action_area()
        action_area.remove(entry)
        # add the label and text entry to a table
        table = gtk.Table(2,2)
        table.attach(label,0,1,0,1)
        table.attach(entry,1,2,0,1)
        table.set_col_spacing(0,10)
        # add the table to the context area
        box = dialog.get_content_area()
        box.pack_start(table,fill=False,expand=False,padding=0)
        box.show_all()
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

    def replace(self):
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

    def goto_line(self):
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

    def run(self):
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
    
    def replace_tabs(self):
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
   
    def toggle_comments(self):
        if self.tabs:
            tab = self.current_tab()
            tab.comment()

    def toggle_mark(self):
        if self.tabs:
            tab = self.current_tab()
            tab.toggle_mark()

    def prev_mark(self):
        if self.tabs:
            tab = self.current_tab()
            tab.prev_mark()

    def next_mark(self):
        if self.tabs:
            tab = self.current_tab()
            tab.next_mark()

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

    def new_tab(self,x=None):
        if self.tabs:
            previous_tab = self.current_tab()
            current_folder = previous_tab.get_current_folder()
        else:
            current_folder = os.curdir
        tab = Tab(self.notebook,self.statusbar,current_folder)
        self.tabs.append(tab)
        self.notebook.set_current_page(len(self.tabs)-1)
        tab.focus()
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
        new_file = False
        try:
            f = open(filename,'r')
            text = f.read()
            f.close()
        except IOError as e:
            text = ""
            new_file = True
        tab = self.current_tab()
        textview = tab.get_textview()
        textbuffer = textview.get_buffer()
        textview.set_sensitive(False)
        textbuffer.set_text(text)
        start = textbuffer.get_start_iter()
        textbuffer.place_cursor(start)
        textview.set_sensitive(True)
        tab.set_filename(filename)
        textbuffer.set_modified(new_file)
        tab.update_statusbar()
        tab.focus()

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


