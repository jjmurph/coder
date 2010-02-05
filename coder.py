#!/usr/bin/env python

import sys
import gtk
import os

class Tab:
    def __init__(self):
       pass 

class TextEditor:
    def __init__(self):
        builder = gtk.Builder()
        builder.add_from_file("coder.glade")
        
        #gtk objects from glade
        self.window = builder.get_object("window")
        self.notebook = builder.get_object("notebook")

        #link the signal handlers
        builder.connect_signals(self)
        
        self.filenames = []
        self.filenames.append("")
        
        self.textviews = []
        self.textviews.append(builder.get_object("textview"))        
        
    ##### signal handlers #####
    def on_window_destroy(self,widget,data=None):
        gtk.main_quit()
        
    def on_menu_item_new_activate(self,widget,data=None):
        self.new_tab()
    
    def on_menu_item_open_activate(self,widget,data=None):
        filename = os.getcwd() + os.sep + 'testfile.txt'
        self.load_file(filename)
        
    ###########################

    def current_page(self):
        return self.notebook.get_current_page()

    def new_tab(self):
        scrolledwindow = gtk.ScrolledWindow()
        scrolledwindow.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
        textview = gtk.TextView()
        textbuffer = textview.get_buffer()
        scrolledwindow.add(textview)
        scrolledwindow.show()
        textview.show()
        label = gtk.Label("New Document")        
        self.notebook.append_page(scrolledwindow,label)
        self.textviews.append(textview)
        self.filenames.append("")
    
    def load_file(self,filename):
        try:
            f = open(filename,'r')
            text = f.read()
            f.close()
            
            textview = self.textviews[self.current_page()]
            textbuffer = textview.get_buffer()
            
            #disable the text view while loading the buffer
            textview.set_sensitive(False)
            
            #store the file's contents in the buffer
            textbuffer.set_text(text)
            textbuffer.set_modified(False)
            
            #turn the text view back on
            textview.set_sensitive(True)
            
            self.filenames[self.current_page()] = filename

            scrolledwindow = textview.get_parent()
            self.notebook.set_tab_label(scrolledwindow,gtk.Label(os.path.basename(filename)))
            
            print("Loaded %s" % filename)
        except IOError as e:          
            print("Couldn't open file %s" % filename)
            
def init():
    cur_dir = os.curdir
    cwd = os.getcwd()
    #print "cur_dir = " + cur_dir
    #print "cwd = " + cwd
            
if __name__ == "__main__":
    init()
    editor = TextEditor()
    editor.window.show()
    gtk.main()


        

