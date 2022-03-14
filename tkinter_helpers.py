# pylint: disable-all
import tkinter as tk
from tkinter import ttk


# Source: https://stackoverflow.com/a/36221216
class CreateToolTip(object):
    """
    create a tooltip for a given widget
    """
    def __init__(self, widget, text='widget info'):
        self.waittime = 500     # milliseconds
        self.wraplength = 180   # pixels
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave)
        self.id = None
        self.tw = None

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.waittime, self.showtip)

    def unschedule(self):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)

    def showtip(self, event=None):
        x = y = 0
        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        # creates a toplevel window
        self.tw = tk.Toplevel(self.widget)
        # Leaves only the label and removes the app window
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(self.tw, text=self.text, justify='left',
                       background="#ffffff", relief='solid', borderwidth=1,
                       wraplength = self.wraplength)
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tw
        self.tw= None
        if tw:
            tw.destroy()


# adapted from https://stackoverflow.com/a/10065345
class Mbox(object):

    def __init__(self, root, title, info, inputs, callback, font=None):
        """
        msg = <str> the message to be displayed
        dict_key = <sequence> (dictionary, key) to associate with user input
        (providing a sequence for dict_key creates an entry for user input)
        """
        self.top = tk.Toplevel(root)
        self.top.title(title)

        frm = ttk.Frame(self.top, borderwidth=4, relief='ridge')
        frm.pack(fill='both', expand=True)

        ttk.Label(frm, text=info, font=font).grid(row=0, column=1, columnspan=2, padx=3, pady=3)

        def clicked(event=None):
            result = callback([entry.get() for entry in entries])
            self.top.destroy()
            return result

        entries = []
        for idx, name in enumerate(inputs):
            ttk.Label(frm, text=name, font=font).grid(row=idx+1, column=1, padx=3, pady=3, sticky='e')
            entry = ttk.Entry(frm)
            entry.grid(row=idx+1, column=2, padx=3, pady=3, sticky='w')
            entry.bind('<Return>', clicked)
            entries.append(entry)

        ttk.Button(
            frm,
            text='Save Image',
            command=clicked
        ).grid(row=len(inputs)+1, column=1, columnspan=2, padx=3, pady=3)

