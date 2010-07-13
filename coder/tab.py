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

import os,sys
import gtk

from coder import SOURCE_VIEW,MAIN_PATH
if SOURCE_VIEW:
    import gtksourceview2

class Tab(object):
    '''
    Manages the Scrolled Window, Text View, Text Buffer, Label, and File
    that make up a tab in the Text Editor.
    '''

    if SOURCE_VIEW:
        source_language_manager = gtksourceview2.language_manager_get_default()
        langs = {'py':'python','glade':'xml','pl':'perl'}
        style_scheme_manager = gtksourceview2.style_scheme_manager_get_default()
        styles_path = os.path.join(MAIN_PATH,'data')
        scheme = None
        if os.path.exists(styles_path):
            style_scheme_manager.prepend_search_path(styles_path)
            style = 'coder'
            scheme = style_scheme_manager.get_scheme(style)
            if not scheme:
                print("Couldn't load style: %s" % style)
        else:
            print("Couldn't find styles directory")

    def __init__(self,notebook,statusbar,starting_folder):
        self.notebook = notebook
        self.statusbar = statusbar
        self.starting_folder = starting_folder
        self.filename = ""
        self.changed = 0
        self.line = 0
        self.col = 0
        self.create_widgets()
        self.marks = []
        self.notebook.append_page(self.window,self.label)
        self.window.show()
        self.textview.show()
    
    def create_widgets(self):
        'Creates the Scrolled Window, Text View, and Label'
        self.window = gtk.ScrolledWindow()
        self.window.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
        if SOURCE_VIEW:
            self.textbuffer = gtksourceview2.Buffer()
            if Tab.scheme:
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

    def get_current_folder(self):
        if self.filename:
            return os.path.dirname(self.filename)
        else:
            return self.starting_folder

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
        Intercepts backspace keypresses and redirect to the backspace function
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
            elif keyname == 'BackSpace':
                return self.backspace()

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
        textmark = self.textbuffer.get_mark('insert')
        self.textview.scroll_mark_onscreen(textmark)

    def backspace(self):
        '''
        If the user hits backspace and there's a tab (4 spaces) behind the
        cursor, delete all 4 of those spaces (the whole tab).
        Else, return False and let the normal signal handler deal with it.
        '''
        tab = '    ' # 4 spaces
        bounds = self.textbuffer.get_selection_bounds()
        if bounds:
            # a block is selected, just do a normal backspace
            return False
        else:
            textiter_end = self.textbuffer.get_iter_at_mark(self.textbuffer.get_insert())
            line = textiter_end.get_line()
            col = textiter_end.get_line_offset() - 4
            if col >= 0:
                textiter = self.textbuffer.get_iter_at_line_offset(line,col)
                text = self.textbuffer.get_text(textiter,textiter_end,True)
                if text == tab:
                    self.textbuffer.delete(textiter,textiter_end)
                    return True
                else:
                    return False
            return False

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
        '''
        Updates the cursor position if it changed.
        '''
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
        self.textview.grab_focus()

    def toggle_mark(self):
        removed = False
        for i in xrange(len(self.marks)):
            if self.line == self.marks[i]:
                del(self.marks[i])
                removed = True
                break
        if not removed:
            added = False
            for i in xrange(len(self.marks)):
                if self.line < self.marks[i]:
                    self.marks.insert(i,self.line)
                    added = True
                    break
            if not added:
                self.marks.append(self.line)

    def next_mark(self):
        mark = None
        for i in xrange(len(self.marks)):
            if self.line < self.marks[i]:
                mark = self.marks[i]
                break
        if self.marks and mark is None:
            mark = self.marks[0]
        if mark is not None:
            iter = self.textbuffer.get_iter_at_line(mark)
            self.textbuffer.place_cursor(iter)
            self.textview.scroll_to_iter(iter,0.1)

    def prev_mark(self):
        mark = None
        for i in xrange(len(self.marks)-1,-1,-1):
            if self.line > self.marks[i]:
                mark = self.marks[i]
                break
        if self.marks and mark is None:
            mark = self.marks[-1]
        if mark is not None:
            iter = self.textbuffer.get_iter_at_line(mark)
            self.textbuffer.place_cursor(iter)
            self.textview.scroll_to_iter(iter,0.1)

