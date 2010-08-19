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

import gtk

def build_main_menu(editor,accelgroup=None):
    menubar = gtk.MenuBar()

    ### File Menu ###
    menu_item = gtk.MenuItem(label='_File',use_underline=True)
    menu = gtk.Menu()
    item = gtk.ImageMenuItem(gtk.STOCK_NEW,accelgroup)
    item.connect('activate',lambda w:editor.new_tab())

    menu.append(item)
    item = gtk.ImageMenuItem(gtk.STOCK_OPEN,accelgroup)
    item.connect('activate',lambda w:editor.file_open())
    menu.append(item)
    item = gtk.ImageMenuItem(gtk.STOCK_SAVE,accelgroup)
    item.connect('activate',lambda w:editor.file_save())
    menu.append(item)
    item = gtk.ImageMenuItem(gtk.STOCK_SAVE_AS,accelgroup)
    item.connect('activate',lambda w:editor.file_save_as())
    menu.append(item)
    item = gtk.ImageMenuItem(gtk.STOCK_CLOSE,accelgroup)
    item.connect('activate',lambda w:editor.close_tab())
    menu.append(item)
    item = gtk.SeparatorMenuItem()
    menu.append(item)
    item = gtk.ImageMenuItem(gtk.STOCK_QUIT,accelgroup)
    item.connect('activate',lambda w:editor.quit())
    menu.append(item)
    menu_item.set_submenu(menu)
    menubar.add(menu_item)

    ### Edit Menu ###
    menu_item = gtk.MenuItem(label='_Edit',use_underline=True)
    menu = gtk.Menu()
    item = gtk.ImageMenuItem(gtk.STOCK_CUT,accelgroup)
    item.connect('activate',lambda w:editor.cut())
    menu.append(item)
    item = gtk.ImageMenuItem(gtk.STOCK_COPY,accelgroup)
    item.connect('activate',lambda w:editor.copy())
    menu.append(item)
    item = gtk.ImageMenuItem(gtk.STOCK_PASTE,accelgroup)
    item.connect('activate',lambda w:editor.paste())
    menu.append(item)
    menu_item.set_submenu(menu)
    menubar.add(menu_item)

    ### Search Menu ###
    menu_item = gtk.MenuItem(label='_Search',use_underline=True)
    menu = gtk.Menu()
    item = gtk.ImageMenuItem(gtk.STOCK_FIND,accelgroup)
    item.connect('activate',lambda w:editor.find())
    menu.append(item)
    item = gtk.ImageMenuItem(gtk.STOCK_FIND_AND_REPLACE,accelgroup)
    item.connect('activate',lambda w:editor.replace())
    menu.append(item)
    item = gtk.ImageMenuItem('_Goto Line')
    image = gtk.image_new_from_stock(gtk.STOCK_JUMP_TO,gtk.ICON_SIZE_MENU)
    item.set_image(image)
    key, mod = gtk.accelerator_parse('<Ctrl>G')
    item.add_accelerator('activate',accelgroup,key,mod,gtk.ACCEL_VISIBLE)
    item.connect('activate',lambda w:editor.goto_line())
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
    item.connect('activate',lambda w:editor.run())
    menu.append(item)
    item = gtk.ImageMenuItem('Replace _Tabs with Spaces')
    image = gtk.image_new_from_stock(gtk.STOCK_GO_FORWARD,gtk.ICON_SIZE_MENU)
    item.set_image(image)
    item.connect('activate',lambda w:editor.replace_tabs())
    menu.append(item)
    item = gtk.ImageMenuItem('Toggle Comments')
    image = gtk.image_new_from_stock(gtk.STOCK_REMOVE,gtk.ICON_SIZE_MENU)
    item.set_image(image)
    key, mod = gtk.accelerator_parse('<Ctrl>D')
    item.add_accelerator('activate',accelgroup,key,mod,gtk.ACCEL_VISIBLE)
    item.connect('activate',lambda w:editor.toggle_comments())
    menu.append(item)
    item = gtk.ImageMenuItem('Toggle Mark')
    image = gtk.image_new_from_stock(gtk.STOCK_REMOVE,gtk.ICON_SIZE_MENU)
    item.set_image(image)
    key, mod = gtk.accelerator_parse('<Ctrl><Alt>M')
    item.add_accelerator('activate',accelgroup,key,mod,gtk.ACCEL_VISIBLE)
    item.connect('activate',lambda w:editor.toggle_mark())
    menu.append(item)
    item = gtk.ImageMenuItem('Prev Mark')
    image = gtk.image_new_from_stock(gtk.STOCK_REMOVE,gtk.ICON_SIZE_MENU)
    item.set_image(image)
    key, mod = gtk.accelerator_parse('<Ctrl><Shift>M')
    item.add_accelerator('activate',accelgroup,key,mod,gtk.ACCEL_VISIBLE)
    item.connect('activate',lambda w:editor.prev_mark())
    menu.append(item)
    item = gtk.ImageMenuItem('Next Mark')
    image = gtk.image_new_from_stock(gtk.STOCK_REMOVE,gtk.ICON_SIZE_MENU)
    item.set_image(image)
    key, mod = gtk.accelerator_parse('<Ctrl>M')
    item.add_accelerator('activate',accelgroup,key,mod,gtk.ACCEL_VISIBLE)
    item.connect('activate',lambda w:editor.next_mark())
    menu.append(item)
    item = gtk.ImageMenuItem('Convert Line Endings')
    image = gtk.image_new_from_stock(gtk.STOCK_REMOVE,gtk.ICON_SIZE_MENU)
    item.set_image(image)
    #key, mod = gtk.accelerator_parse('<Ctrl>M')
    #item.add_accelerator('activate',accelgroup,key,mod,gtk.ACCEL_VISIBLE)
    item.connect('activate',lambda w:editor.convert_line_endings())
    menu.append(item)
    menu_item.set_submenu(menu)
    menubar.add(menu_item)
    
    return menubar

