import sys
from gtk import *

import gpgpathconfig
import pathdb
import findpath
import gpg

def destroy(args):
    mainquit()

class PathWindow(GtkWindow):
    def __init__(self):
        global trusted

        GtkWindow.__init__(self)
        self.set_border_width(8)
        self.connect("destroy", destroy)
        
        vbox = GtkVBox()

        lbl = GtkLabel("Your key ID")
        lbl["xalign"] = 0.0
        lbl.show()
        vbox.pack_start(lbl, expand = 0)

        mykey = GtkEntry()
        mykey.set_name("mykey")
        mykey.set_text(str(trusted))
        mykey.set_editable(0)
        mykey.show()
        vbox.pack_start(mykey, expand = 0)

        lbl = GtkLabel("Target key ID")
        lbl["xalign"] = 0.0
        lbl.show()
        vbox.pack_start(lbl, expand = 0)

        self.target = GtkEntry()
        self.target.set_name("target")
        self.target.show()
        vbox.pack_start(self.target, expand = 0)

        lbl = GtkLabel("Avoid")
        lbl["xalign"] = 0.0
        lbl.show()
        vbox.pack_start(lbl, expand = 0)

        self.avoid = GtkEntry()
        self.avoid.set_name("avoid")
        self.avoid.show()
        vbox.pack_start(self.avoid, expand = 0)

        sep = GtkHSeparator()
        sep.show()
        vbox.pack_start(sep, expand = 0, padding = 4)

        self.pathview = GtkScrolledWindow()
        self.pathview.set_policy(POLICY_AUTOMATIC, POLICY_AUTOMATIC)

        self.pathlist = GtkCList(cols = 2)
        self.pathlist.show()
        self.pathview.add_with_viewport(self.pathlist)

        vbox.pack_start(self.pathview)

        buttons = GtkHButtonBox()
        buttons.set_layout_default(BUTTONBOX_END)
        buttons.set_border_width(8)
        buttons.show()

        b1 = GtkButton('Search')
        b1.connect('clicked', search)
        b1.show()
        buttons.pack_start(b1)

        b1 = GtkButton('Quit')
        b1.connect('clicked', mainquit)
        b1.show()
        buttons.pack_start(b1)

        vbox.pack_start(buttons, expand = 0)
        vbox.show()

        self.add(vbox)

    def clear_path(self):
        self.pathlist.clear()
        self.pathview.show()

    def add_key(self, key, desc):
        self.pathlist.append([key, desc])
        self.pathlist.columns_autosize()

def search(data = None):
    target = win.target.get_text()
    avoid = win.avoid.get_text().split(" ")
    try:
        avoid.remove('')
    except:
        pass
    print target
    target_key = long(target, 16)
    trusted_key = long(trusted, 16)
    win.clear_path()
    print "avoid", avoid
    forbidden = [long(f, 16) for f in avoid]
    path = findpath.find_path(target_key, trusted_key, forbidden)
    findpath.print_path(path)
    path.reverse()
    for key in path:
        keys = gpg.get_keys("%08X" % key)
        print "%s -> %s" % (key, keys)
        if len(keys) == 0:
            desc = "not found"
        elif len(keys) == 1:
            desc = keys[0].uid.encode("latin-1", "replace")
        else:
            desc = "Multiple matches"
        win.add_key("%08X" % key, desc)

if __name__ == '__main__':
    global trusted, win
    pathdb.init()
    trusted = "EB144031"

    win = PathWindow()
    win.show()
    mainloop()
