#!/usr/bin/env python

import sys
import gtk
import os

class Tab(object):
    '''
    Manages the Scrolled Window, Text View, Text Buffer, Label, and File
    that make up a tab in the Text Editor.
    '''

    def __init__(self,notebook,window=None,textview=None,label=None):
        '''
        The first tab is built by Glade, we just need to store the widgets.
        Subsequent tabs are built dynamically, only the notebook
        argument should be used for those.
        '''

        self.notebook = notebook
        self.filename = ""

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
        self.textview = gtk.TextView()
        self.textbuffer = self.textview.get_buffer()
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
        'Sets the filename and updates the label'
        self.filename = filename
        self.label.set_text(os.path.basename(filename))
        self.notebook.set_tab_label(self.window,self.label)
 

class TextEditor(object):
    def __init__(self):
        builder = gtk.Builder()
        builder.add_from_file("coder.glade")
        
        #gtk objects from glade
        self.window = builder.get_object("window")
        self.notebook = builder.get_object("notebook")
        
        scrolledwindow = builder.get_object("scrolledwindow")
        textview = builder.get_object("textview")
        #label = builder.get_object("label")
        label = gtk.Label("New Document")

        #link the signal handlers
        builder.connect_signals(self)
       
        self.tabs = [] #list of all active tabs
        tab = Tab(self.notebook,scrolledwindow,textview,label)
        self.tabs.append(tab)
        
    ##### signal handlers #####

    def on_window_destroy(self,widget,data=None):
        gtk.main_quit()
        
    def on_menu_item_new_activate(self,widget,data=None):
        self.new_tab()
        self.notebook.set_current_page(len(self.tabs)-1)
    
    def on_menu_item_open_activate(self,widget,data=None):
        filename = os.getcwd() + os.sep + 'testfile.txt'
        self.load_file(filename)
        
    ###########################

    def current_page(self):
        return self.notebook.get_current_page()

    def current_tab(self):
        return self.tabs[self.current_page()]

    def new_tab(self):
        tab = Tab(self.notebook)
        self.tabs.append(tab)
    
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
           
            print("Loaded %s" % filename)
        except IOError as e:          
            print("Couldn't open file %s" % filename)

def main():
    editor = TextEditor()
    editor.window.show()
    gtk.main()

if __name__ == "__main__":
    main()
        

