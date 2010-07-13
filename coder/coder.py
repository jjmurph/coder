#!/usr/bin/env python

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

MAIN_PATH = os.path.normpath(os.path.join(os.path.abspath(sys.argv[0]),os.pardir,os.pardir))

def main(filenames=[]):
    '''
    Creates the Text Editor object and starts GTK.
    Accepts an optional list of filenames to pass to the Text Editor
    '''
    from editor import TextEditor
    editor = TextEditor(filenames)
    gtk.main()

if __name__ == "__main__":
    filenames = sys.argv[1:]
    main(filenames)
