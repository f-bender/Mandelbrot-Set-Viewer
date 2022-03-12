from argparse import ArgumentParser
import threading
import time
import tkinter as tk
from tkinter import ttk
import numpy
from PIL import Image, ImageTk

from mandelbrot_iterations_calculator import get_image_array
from tkinter_helpers import CreateToolTip

class FractalFrame(tk.Frame): # pylint: disable=too-many-ancestors, too-many-instance-attributes
    ''' A class for showing mandelbrot-set-like fractals in a tkinter frame
    '''

    MIN_SIZE = (600, 400) # pixels
    REDRAW_DELAY = 0.5 # seconds
    RECT_THICKNESS = 2 # pixels
    RECT_COLOR = 'gray'
    MIN_RECT_WIDTH = 6

    class ControlPanel(tk.Frame): # pylint: disable=too-many-ancestors
        ''' A panel to control some values related to the displayed fractal
        '''

        CHAR_WIDTH = 8
        ENTRY_WIDTH = 22
        DEFAULT_FONT = 'Helvetica 12'
        HEADER_FONT = 'Helvetica 12 bold'

        ARROW_ADJUSTMENT_FACTOR = 1.1

        def __init__(self, master):
            super().__init__(master)

            # Building a grid of control widgets:

            ##     Center location:    |    Zoom Level     <Entry>
            ##     Real Part   <Entry> |    Iterations     <Entry>
            ##  Imaginary Part <Entry> | Color Cycle Speed <Entry>

            ttk.Label(self, text='Center location:', font=self.HEADER_FONT).grid(column=1, row=1, columnspan=2, padx=5, pady=2)

            ttk.Label(self, text='Real Part', font=self.DEFAULT_FONT).grid(column=1, row=2, padx=5, pady=2)
            self.center_real_entry = ttk.Entry(self, width=self.ENTRY_WIDTH)
            self.center_real_entry.grid(column=2, row=2, sticky='w', padx=5, pady=2)

            ttk.Label(self,text='Imaginary Part', font=self.DEFAULT_FONT).grid(column=1, row=3, padx=5, pady=2)
            self.center_imaginary_entry = ttk.Entry(self, width=self.ENTRY_WIDTH)
            self.center_imaginary_entry.grid(column=2 ,row=3, sticky='w', padx=5, pady=2)

            ttk.Label(self,text='Zoom Level', font=self.DEFAULT_FONT).grid(column=4, row=1, padx=5, pady=2)
            self.zoom_level_entry = ttk.Entry(self, width=self.ENTRY_WIDTH)
            self.zoom_level_entry.grid(column=5, row=1, sticky='w', padx=5, pady=2)

            ttk.Separator(self, orient=tk.VERTICAL).grid(column=3, row=1, rowspan=3, sticky='ns', padx=5, pady=2)

            iterations_label = ttk.Label(self,text='Iterations', font=self.DEFAULT_FONT)
            iterations_label.grid(column=4, row=2, padx=5, pady=2)
            CreateToolTip(
                iterations_label,
                ('The number of iterations to do before condluding that the value in question is inside the Mandelbrot Set (and is colored black). '
                 'Higher values result in a more accurate picture but take longer to calculate.')
            )
            self.iterations_entry = ttk.Entry(self, width=self.ENTRY_WIDTH)
            self.iterations_entry.grid(column=5, row=2, sticky='w', padx=5, pady=2)

            color_cycle_speed_label = ttk.Label(self,text='Color Cycle Speed:', font=self.DEFAULT_FONT)
            color_cycle_speed_label.grid(column=4,row=3, padx=5, pady=2)
            CreateToolTip(
                color_cycle_speed_label,
                ('The speed at which colors change in relation to the number of iterations that have to be made before the value explodes. '
                 'Lower values result in a more gradual change, higher values result in a more drastic change of colors.')
            )
            self.color_cycle_speed_entry = ttk.Entry(self,width=self.ENTRY_WIDTH)
            self.color_cycle_speed_entry.grid(column=5,row=3,sticky='w', padx=5, pady=2)

            # center align columns 1-5 by adding weighted empty columns left and right
            self.grid_columnconfigure(0, weight=1)
            self.grid_columnconfigure(6, weight=1)

            self._padx = 10
            self._pady = 10
            self.configure(padx=self._padx,pady=self._pady)

            for entry in (self.center_real_entry, self.center_imaginary_entry, self.zoom_level_entry, self.iterations_entry, self.color_cycle_speed_entry):
                entry.bind('<Key>', self.adjust_entry)
                entry.bind('<Return>', self.master.update_values)

            self.update_values()

        def adjust_entry(self, event):
            if event.keycode not in (38, 40):
                return

            entry = event.widget
            current_value = entry.get()
            entry.delete(0, tk.END)
            if event.keycode == 38:
                # arrow up / right
                new_value = float(current_value) * self.ARROW_ADJUSTMENT_FACTOR
            else:
                # arrow down / left
                new_value = float(current_value) / self.ARROW_ADJUSTMENT_FACTOR

            if current_value.isdecimal():
                new_value = int(new_value)
            entry.insert(tk.END, new_value)

            self.master.update_values()

        def get_required_height(self):
            return self.grid_bbox()[3] + 2 * self._pady

        def update_values(self):
            updated_entries = {
                self.center_real_entry: self.master.z_center.real,
                self.center_imaginary_entry: self.master.z_center.imag,
                self.zoom_level_entry: '%.4g' % self.master.zoom_level,
                self.iterations_entry: self.master.iterations,
                self.color_cycle_speed_entry: self.master.color_cycle_speed,
            }

            for entry, new_value in updated_entries.items():
                entry.delete(0, tk.END)
                entry.insert(tk.END, new_value)

        def get_values(self):
            return {
                'center': complex(float(self.center_real_entry.get()), float(self.center_imaginary_entry.get())),
                'zoom_level': float(self.zoom_level_entry.get()),
                'iterations': int(self.iterations_entry.get()),
                'color_cycle_speed': float(self.color_cycle_speed_entry.get()),
            }

    def __init__(
        self,
        master,
        iterations=500,
        color_cycle_speed=5.0,
        zoom_level=0.3333,
        z_center=-0.7+0j,
    ):
        super().__init__(master)

        self.master.minsize(*self.MIN_SIZE)

        self.iterations = iterations
        self.color_cycle_speed = color_cycle_speed
        self.z_width = 1 / zoom_level
        self.z_center = z_center
        self.rect_width = 100

        self.master = master
        self.window_width = self.window_height = self.canvas_height = -1

        self.canvas = tk.Canvas(self)
        self.canvas.pack()
        self.control_panel = self.ControlPanel(self)
        self.control_panel.pack()

        self.canvas.bind('<Button-1>', self.zoom_in_draw)
        self.canvas.bind('<Button-3>', self.zoom_out_draw)
        self.canvas.bind('<MouseWheel>', self.zoom_rect)
        self.canvas.bind('<Motion>', self.new_rectangle)
        self.canvas.bind('<Leave>', self.new_rectangle)
        self.master.bind('<Configure>', self.resize)

        self.last_parameters = {}
        self.last_ccs = 0

        self.rectangle = None
        self.current_view = None

        self.displayed_image = None
        self.cropped = None
        
        self.resize_thread = None
        self.time_of_resize_drawing = None

        self.default_parameters = (self.z_width, self.z_center, self.iterations)

    def update_values(self, event=None): # pylint: disable=unused-argument
        control_panel_values = self.control_panel.get_values()
        
        self.z_center = control_panel_values['center']
        self.z_width = 1 / control_panel_values['zoom_level']
        self.iterations = control_panel_values['iterations']
        self.color_cycle_speed = control_panel_values['color_cycle_speed']

        self.control_panel.update_values()

        self.draw()


    def resized_draw(self):
        while True:
            # wait until the resizing process has finished
            if time.time() > self.time_of_resize_drawing:
                break

        if self.window_height != self.master.winfo_height() or self.window_width != self.master.winfo_width():
            self.window_width = self.master.winfo_width()
            self.window_height = self.master.winfo_height()
            self.canvas_height = self.window_height - self.control_panel.get_required_height()
            self.rect_width = min(self.rect_width, self.window_width)

            self.place(x=0, y=0, width=self.window_width, height=self.window_height)
            self.canvas.place(x=0, y=0, width=self.window_width, height=self.canvas_height)
            self.control_panel.place(x=0, width=self.window_width, y=self.canvas_height, height=self.control_panel.get_required_height())

            self.draw()


    def resize(self, event):
        # check whether the size was actually changed
        if event.width != self.window_width or event.height != self.window_height:
            # only draw after there was no resize event for a certain delay,
            # to avoid costly drawing of many frames while the window is actively being resized
            self.time_of_resize_drawing = time.time() + self.REDRAW_DELAY

            if not self.resize_thread or not self.resize_thread.is_alive():
                self.resize_thread = threading.Thread(target=self.resized_draw)
                self.resize_thread.start()

    def draw(self):
        if self.last_parameters:
            same_size = self.window_width == self.last_parameters['width'] and self.canvas_height == self.last_parameters['height']
            same_center = \
                abs(self.z_center.real - self.last_parameters['z_center'].real) / self.z_width < 1 / (2*self.window_width) and \
                abs(self.z_center.imag - self.last_parameters['z_center'].imag) / self.z_width < 1 / (2*self.window_width)
            same_z_width = abs(self.z_width - self.last_parameters['z_width']) / self.z_width < 1 / (2*self.window_width)

            same_iterations = self.iterations == self.last_parameters['iterations']
        else:
            same_size = same_center = same_z_width = same_iterations = False

        same_position = same_size and same_center and same_z_width

        if not same_position:
            self.last_parameters['width'] = self.window_width
            self.last_parameters['height'] = self.canvas_height
            self.last_parameters['z_width'] = self.z_width
            self.last_parameters['z_center'] = self.z_center
        if not same_iterations:
            self.last_parameters['iterations'] = self.iterations

        # TODO don't tell the image creator "same pos", "same iters", or "same colors", but explicitly tell him which optimizations to apply (which is determined from same_pos, same_iters, same_colors)
        start = time.time()
        array = get_image_array(
            self.window_width,
            self.canvas_height,
            self.z_center,
            self.z_width,
            self.iterations,
            self.color_cycle_speed,
            same_position,
            same_iterations
        )
        print(f'Image generated in {time.time() - start:.3f} seconds', end='     \r')

        old_view = self.current_view
        image = Image.fromarray(numpy.swapaxes(array, 0, 1), mode='HSV')
            
        self.displayed_image = ImageTk.PhotoImage(image)
        self.current_view = self.canvas.create_image(0, 0, image=self.displayed_image, anchor=tk.NW)
        if old_view is not None:
            self.canvas.delete(old_view)
        if self.rectangle is not None:
            self.canvas.tag_raise(self.rectangle)


    def new_rectangle(self,event):
        if self.rectangle is not None:
            self.canvas.delete(self.rectangle)
        if event is not None and 'Leave event' not in str(event):
            self.rectangle = self.canvas.create_rectangle(*self.get_rect_coords(event), outline=self.RECT_COLOR, width=self.RECT_THICKNESS)

            # why this is necessary: https://stackoverflow.com/questions/46060570/tkinter-the-shape-isnt-uniform-and-the-animation-looks-bad
            # especially https://stackoverflow.com/a/54954035 explains it well
            self.canvas.configure(bg='black')


    def get_rect_coords(self, event):
        return (event.x-self.rect_width/2,  event.y-self.rect_width*self.canvas_height/self.window_width/2,
                event.x+self.rect_width/2,  event.y+self.rect_width*self.canvas_height/self.window_width/2)


    def zoom_rect(self, event):
        if event.delta < 0:
            self.rect_width = min(self.rect_width*1.15, self.window_width)
        else:
            self.rect_width = max(self.rect_width/1.15, self.MIN_RECT_WIDTH)

        self.new_rectangle(event)


    def zoom_out_draw(self, event):
        control_panel_values = self.control_panel.get_values()

        x_offset, y_offset = event.x - self.window_width / 2, self.canvas_height / 2 - event.y
        self.z_center -= complex(x_offset * self.z_width / self.rect_width, y_offset * self.z_width / self.rect_width)
        self.z_width *= self.window_width / self.rect_width

        self.iterations = control_panel_values['iterations']
        self.color_cycle_speed = control_panel_values['color_cycle_speed']

        self.control_panel.update_values()
        self.draw()


    def zoom_in_draw(self, event):
        control_panel_values = self.control_panel.get_values()

        x_offset, y_offset = event.x - self.window_width / 2, self.canvas_height / 2 - event.y
        self.z_center += complex(x_offset * self.z_width / self.window_width, y_offset * self.z_width / self.window_width)
        self.z_width *= self.rect_width / self.window_width

        self.iterations = control_panel_values['iterations']
        self.color_cycle_speed = control_panel_values['color_cycle_speed']

        self.control_panel.update_values()
        self.draw()


    def reset_view(self):
        self.z_width, self.z_center, self.iterations = self.default_parameters
        self.draw()


    @property
    def zoom_level(self):
        return 1 / self.z_width



def main():
    parser = ArgumentParser()
    parser.add_argument('--width', '-W', type=int, default=600, help='Width of the window')
    parser.add_argument('--height', '-H', type=int, default=600, help='Height of the window')
    parser.add_argument('--fullscreen', '-f', action='store_true',
        help='whether to start in fullscreen mode (in which case width and height are ignored)'
    )
    parser.add_argument('--center', '-c', type=float, nargs=2, default=[-0.7, 0],
        help='real and imaginary part of the initial image center'
    )
    parser.add_argument('--zoom_level', '-z', type=float, default=1/3,
        help='how far zoomed in the image should be initially'
    )
    parser.add_argument('--iterations', '-i', type=int, default=500,
        help='the number of iterations to do before condluding that the value in question is inside the Mandelbrot Set'
    )
    args = parser.parse_args()

    root = tk.Tk()
    root.title('Mandelbrot Set')
    root.protocol('WM_DELETE_WINDOW', root.destroy)
    if args.fullscreen:
        root.attributes('-fullscreen', True)
    else:
        root.geometry(f'{args.width}x{args.height}')

    FractalFrame(
        master=root,
        z_center=complex(args.center[0], args.center[1]),
        zoom_level=args.zoom_level,
        iterations=args.iterations
    ).pack()

    root.mainloop()


if __name__ == '__main__':
    main()
