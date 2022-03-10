import tkinter as tk
from tkinter import ttk
from tkinter_helpers import CreateToolTip
from PIL import Image, ImageTk
import numpy
import time
from colormap import Colormap
import mandelbrot_image_cuda as image_creator
import threading
from math import ceil, log2

class FractalFrame(tk.Frame): # pylint: disable=too-many-ancestors
    ''' A class for showing mandelbrot-set-like fractals in a tkinter frame
    '''

    class ControlPanel(tk.Frame): # pylint: disable=too-many-ancestors
        ''' A panel to control some values related to the displayed fractal
        '''

        CHAR_WIDTH = 8
        ENTRY_WIDTH = 22
        SCALE_LENGTH = 200
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

            # center align columns 1-5
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
            return self.grid_bbox()[3] + 2*self._pady

        def update_values(self):
            updated_entries = {
                self.center_real_entry: self.master.z_center.real,
                self.center_imaginary_entry: self.master.z_center.imag,
                self.zoom_level_entry: '%.4g' % self.master.get_zoom_level(),
                self.iterations_entry: self.master.iterations,
                self.color_cycle_speed_entry: self.master.color_cycle_speed,
            }

            for entry, new_value in updated_entries.items():
                entry.delete(0, tk.END)
                entry.insert(tk.END, new_value)
        
        def resize(self):
            # time.sleep(0.01)
            self.center_real_entry.config(width=self.ENTRY_WIDTH)
            self.center_imaginary_entry.config(width=self.ENTRY_WIDTH)
            self.zoom_level_entry.config(width=self.ENTRY_WIDTH)
            self.iterations_entry.config(width=self.ENTRY_WIDTH)
            self.color_cycle_speed_entry.config(width=self.ENTRY_WIDTH)
            # self.color_cycle_speed.config(length=self.SCALE_LENGTH)
            # self.color_cycle_speed2.config(length=self.SCALE_LENGTH)
            if self.grid_bbox()[2] > self.winfo_width():
                print(self.grid_bbox()[2], self.winfo_width())
                rest_width = self.winfo_width() - self.grid_bbox(1,0,1,0)[2] - self.grid_bbox(4,0,4,0)[2]
                reduced_width = int(rest_width/2/self.CHAR_WIDTH)
                self.center_real_entry.config(width=reduced_width)
                self.center_imaginary_entry.config(width=reduced_width)
                self.zoom_level_entry.config(width=reduced_width)
                self.iterations_entry.config(width=reduced_width)
                self.color_cycle_speed_entry.config(width=reduced_width)
                # self.color_cycle_speed.config(length=rest_width/2)
                # self.color_cycle_speed2.config(length=rest_width/2)


        def get_values_scale(self):
            return (
                complex(float(self.center_real_entry.get()), float(self.center_imaginary_entry.get())),
                1/float(self.zoom_level_entry.get()),
                int(self.iterations_entry.get()),
                float(self.color_cycle_speed_entry.get())
                # 2**float(self.color_cycle_speed.get()) * float(self.color_cycle_speed2.get())
            )

        def get_values(self):
            return (
                complex(float(self.center_real_entry.get()), float(self.center_imaginary_entry.get())),
                1/float(self.zoom_level_entry.get()),
                int(self.iterations_entry.get()),
                float(self.color_cycle_speed_entry.get())
            )





    def __init__(self,master=None,width=1000, height=1000, iterations=200, color_cycle_speed=5.0, zoom_level=0.25, z_center=0+0j,
                colormap=Colormap([(255,0,0),(255,255,0),(0,255,0),(0,255,255),(0,0,255),(255,0,255)] ,cyclic=True), processes=None, fluid_animation=False):
        assert width >= 300 and height >= 200 , 'Minimum dimensions are 300x200'
        super().__init__(master)
        if processes is None:
            self.processes = 1
        else:
            self.processes = processes
        self.fluid_animation = fluid_animation
        self.master = master
        # self.master_image_getter = get_image_array
        self.complete_height = height
        # height of the image (the Frame without the control panel)
        self.height = int(min(0.9*self.complete_height,self.complete_height-100))
        self.width = width
        self.colormap = colormap
        self.iterations = iterations
        self.color_cycle_speed = color_cycle_speed
        self.canvas = tk.Canvas(self, width=width, height=height)
        # ttk.Label(self, text = 'Length:').grid(row = 1, column = 2, pady=2)
        self.canvas.pack()
        self.z_width = 1/zoom_level
        self.z_center = z_center
        self.rect_width = width/10
        # Control Panel: a frame on the right side of this FractalFrame, to have some direct 
        # control over and display of the parameters (e.g. zoom_level, z-center, iterations)
        self.control_panel = self.ControlPanel(self)
        self.control_panel.place(x=0, width=self.width, y=self.height, height=self.complete_height-self.height)

        self.image = None
        self.photo_image = None
        self.cropped = None
        

        self.default_parameters = (self.z_width, self.z_center, self.iterations)

        self.rectangle = self.canvas.create_rectangle(-self.rect_width, -self.rect_width*self.height/self.width,0,0, outline='gray',width=2)
        self.current_view = None
        # self.draw()

        self.canvas.bind('<Button-1>', self.zoom_in_draw)
        self.canvas.bind('<Button-3>', self.zoom_out_draw)
        self.canvas.bind('<MouseWheel>', self.zoom_rect)
        self.canvas.bind('<Motion>', self.new_rectangle)
        self.canvas.bind('<Leave>', self.new_rectangle)
        self.master.bind('<Configure>', self.resize)

        self.master.bind('<Key>', self.keydown)

        self.time_of_resize_drawing = time.time()
        # self.time_of_last_resize = time.time()
        self.resize_thread = threading.Thread(target=self.resized_draw,args=(True,))
        self.refresh_thread = None
        # self.resize_event = None
        self.resize_thread.start()

        self.last_parameters = tuple()
        self.last_ccs = 0

    def keydown(self,event):
        if event.char == 'a':
            # if not self.refresh_thread or not self.refresh_thread.is_alive():
            #     self.refresh_thread = threading.Thread(target=self.animate_colors, args=(3,2))
            #     self.refresh_thread.start()
            self.animate_colors(self.color_cycle_speed, self.color_cycle_speed * 50, 0.01)
            return

    def animate_colors(self, start, stop, speed):
        assert stop > start and speed > 0, 'stop > start and speed > 0 has to hold true'
        print('GO!')
        self.color_cycle_speed = start
        while self.color_cycle_speed < stop:
            self.draw()
            self.canvas.update()
            self.color_cycle_speed *= speed + 1
            # time.sleep(1/framerate)
            print(float('%.4g' % self.color_cycle_speed), end='\t\t\t')
        self.control_panel.update_values()

    def update_ccs(self, value):
        if self.last_ccs > float(value):
            self.control_panel.color_cycle_speed2.set(2.0)
        else:
            self.control_panel.color_cycle_speed2.set(1.0)
        self.last_ccs = float(value)
        self.color_cycle_speed = 2**float(value) * float(self.control_panel.color_cycle_speed2.get())
        self.draw(same_pos=True)

    def update_ccs2(self, value):
        self.color_cycle_speed = 2**float(self.control_panel.color_cycle_speed.get()) * float(value)
        self.draw(same_pos=True)

    def update_values(self, event=None):
        print('called update values')
        if self.refresh_thread is None or not self.refresh_thread.is_alive():
            same_pos = False
            if self.z_center == self.control_panel.get_values()[0] and self.control_panel.get_values()[1] == 1/float('%.4g' % self.get_zoom_level()):
                same_pos = True
            self.z_center, self.z_width, self.iterations, self.color_cycle_speed = self.control_panel.get_values()
            self.control_panel.update_values()
            # self.control_panel.update_scale()
            print('now draw')
            self.draw(same_pos=same_pos)
            print('done')

    def resized_draw(self,init=False):
        if not init:
            while True:
                if time.time() > self.time_of_resize_drawing and (self.refresh_thread is None or not self.refresh_thread.is_alive()):
                    break

        if self.complete_height != self.master.winfo_height() or self.width != self.master.winfo_width() or init:
            # while True: # emulated do while (do ... while self.resize_again)
            self.complete_height = self.master.winfo_height()
            # self.height = int(min(0.9*self.complete_height,self.complete_height-100))
            self.height = self.complete_height-self.control_panel.get_required_height()
            self.width = self.master.winfo_width()
            self.rect_width = min(self.rect_width, self.width)

            self.place(x=0,y=0,width=self.width,height=self.complete_height)
            self.canvas.place(x=0,y=0,width=self.width, height=self.height)
            self.control_panel.place(x=0, width=self.width, y=self.height, height=self.control_panel.get_required_height())

            self.control_panel.resize()

            # self.resize_again = False
            self.draw()

            # if not self.resize_again:
            #     break

    def resize(self,event):
        if event.width != self.width or event.height != self.complete_height:
            self.time_of_resize_drawing = time.time() + 1
            if not self.resize_thread.is_alive():
                self.resize_thread = threading.Thread(target=self.resized_draw)
                self.resize_thread.start()


    # def get_image(self,width=None, height=None, iterations=None):
    #     if None in {width, height, iterations}:
    #         width, height, iterations = self.width, self.height, self.iterations

    #     start = time.time()
    #     array = image_creator.get_image_array(width, height, self.z_center, self.z_width, iterations, self.colormap, self.color_cycle_speed, self.processes)
    #     self.refresh_thread = threading.Thread(target=self.redraw, args=(start,numpy.swapaxes(array,0,1)))
    #     self.refresh_thread.start()
    #     # print(f"Took {'%.2f' % (time.time()-start)} seconds to load image.")
       
    #     return ImageTk.PhotoImage(Image.fromarray(numpy.swapaxes(array,0,1)))

    def draw(self,event=None,width=None, height=None, iterations=None, same_pos=False, out=False, colors_changed=False):
        if self.refresh_thread is None or not self.refresh_thread.is_alive():
            if None in {width, height, iterations}:
                width, height, iterations = self.width, self.height, self.iterations

            # zoom_out_box = self.get_rect_coords(event) if out and not colors_changed else None

            same_pos = self.last_parameters and self.last_parameters[:4] == (width, height, self.z_center, 1/float('%.4g' % self.get_zoom_level()))
            same_iters = self.last_parameters and self.last_parameters[4] == iterations
            same_colors = self.last_parameters and self.last_parameters[5:7] == (self.colormap, self.color_cycle_speed)
            self.last_parameters = (width, height, self.z_center, 1/float('%.4g' % self.get_zoom_level()), iterations, self.colormap, self.color_cycle_speed)

            start = time.time()
            array = image_creator.get_image_array(width, height, self.z_center, 1/float('%.4g' % self.get_zoom_level()), iterations, self.colormap, self.color_cycle_speed,same_pos,same_iters,same_colors)#, self.processes, zoom_out_box)
            # TODO: do this with an async Coroutine (something like JS's setInterval() instead of time.sleep()?) to prevent flickering!
            # self.refresh_thread = threading.Thread(target=self.redraw, args=(start,numpy.swapaxes(array,0,1),event, same_pos, out, colors_changed))
            # self.refresh_thread.start() # <- without cuda
            
            # <cuda stuff>
            print(time.time()-start,'seconds')
            old_view = self.current_view
            if same_pos and same_colors:
                mask = self.image.convert('L')              # make it grayscale
                mask = mask.point(lambda p: p > 0 and 255)  # make all pixels with values above 0 white
                self.image = Image.composite(self.image, Image.fromarray(numpy.swapaxes(array,0,1),mode='HSV'), mask)
            else:
                self.image = Image.fromarray(numpy.swapaxes(array,0,1),mode='HSV')
                
            self.photo_image = ImageTk.PhotoImage(self.image)
            self.current_view = self.canvas.create_image(0,0,image=self.photo_image, anchor=tk.NW)
            if old_view is not None:
                    self.canvas.delete(old_view) 
            self.canvas.tag_raise(self.rectangle)
            # </cuda stuff>

            # self.control_panel.update_scale()
            print('drawn',int(time.time()%100))



        # old_view = self.current_view
        # self.image = self.get_image()
        # self.current_view = self.canvas.create_image(0,0,image=self.image, anchor=tk.NW)
        # self.canvas.tag_raise(self.rectangle)
        # self.control_panel.update_values()
        # if old_view is not None:
        #     self.canvas.delete(old_view)
        # self.new_rectangle(event)

    # TODO: make the image_creator not calculate those pixels since they are already known?
    # problem: then I don't know the iterations for that area which means i can not easily change the colors
    def redraw(self,start,array,event, same_pos=False, out=False, colors_changed=False):
        if same_pos: 
            self.cropped = self.image
        elif self.image is not None and event is not None:
            if out:
                # TODO: make the image_creator not calculate those pixels since they are already known
                self.cropped = Image.new('RGB', (self.width, self.height))                                      
                                                                    #this "+1" is a hack to get the black line to disappear when rightclicking while rect_width == width
                self.cropped.paste(self.image.resize((ceil(self.rect_width)+1,ceil(self.rect_width*self.height/self.width)),Image.NEAREST), box=(ceil(self.get_rect_coords(event)[0]),ceil(self.get_rect_coords(event)[1])))
            else:
                self.cropped = self.image.crop(self.get_rect_coords(event)).resize((self.width, self.height),Image.NEAREST)
        else:
            self.cropped = None

        if self.fluid_animation:
            delay = 0.05
        else:
            delay = min(array.shape[0]*array.shape[1] / 500_000, 4)
        while not image_creator.is_done():
            # NOTE:evtl besser so etwas wie clock.tick(), zumindest für fluid_animation
            time.sleep(delay)
            old_view = self.current_view

            # t = time.time()

            self.image = Image.fromarray(array)
            if self.cropped is not None:
                # mask = Image.fromarray(numpy.where(numpy.all(array==0, axis=2),0,1), mode='1') # unsuccessful attempt
                mask = self.image.convert('L')              # make it grayscale
                mask = mask.point(lambda p: p > 0 and 255)  # make all pixels with values above 0 white
                self.image = Image.composite(self.image, self.cropped, mask)
                # self.image = mask

            self.photo_image = ImageTk.PhotoImage(self.image)
            self.current_view = self.canvas.create_image(0,0,image=self.photo_image, anchor=tk.NW)
            if old_view is not None:
                    self.canvas.delete(old_view) 
            self.canvas.tag_raise(self.rectangle)

            # print(f"Took {'%.5f' % (time.time()-t)} for cycle") 

        old_view = self.current_view
        self.image = Image.fromarray(array)
        if out and not colors_changed:
            assert self.cropped is not None, 'cropped is None while zooming out!'
            mask = self.image.convert('L')              # make it grayscale
            mask = mask.point(lambda p: p > 0 and 255)  # make all pixels with values above 0 white
            self.image = Image.composite(self.image, self.cropped, mask)

        self.photo_image = ImageTk.PhotoImage(self.image)
        self.current_view = self.canvas.create_image(0,0,image=self.photo_image, anchor=tk.NW)
        if old_view is not None:
                self.canvas.delete(old_view) 
        self.canvas.tag_raise(self.rectangle)
        
        es = 'es'
        s = ''
        print(f"Took {'%.2f' % (time.time()-start)} seconds to load image. ({self.processes} process{es if self.processes > 1 else s})")


    # def redraw(self,event=None):
    #     # self.view = self.canvas.create_image(0,0,image=self.current_view, anchor=tk.NW)
    #     if event is not None and "Leave event" not in str(event):
    #         # self.canvas.create_rectangle(event.x-self.rect_width/2,  event.y-self.rect_width*self.height/self.width/2,
    #         #      event.x+self.rect_width/2,  event.y+self.rect_width*self.height/self.width/2, outline='gray',width=2)
    #         self.canvas.coords(self.rectangle,(event.x-self.rect_width/2,  event.y-self.rect_width*self.height/self.width/2,
    #              event.x+self.rect_width/2,  event.y+self.rect_width*self.height/self.width/2))
    #         # self.canvas.move(self.rectangle, event.x-x, event.y-y)

    def new_rectangle(self,event):
        self.canvas.delete(self.rectangle)
        if event is not None and 'Leave event' not in str(event):
            coords = self.get_rect_coords(event)
            self.rectangle = self.canvas.create_rectangle(coords[0],coords[1],coords[2],coords[3], outline='gray',width=2)

            # why this is necessary: https://stackoverflow.com/questions/46060570/tkinter-the-shape-isnt-uniform-and-the-animation-looks-bad
            # especially https://stackoverflow.com/a/54954035 explains it well
            self.canvas.configure(bg='black')

    def get_rect_coords(self, event):
        return (event.x-self.rect_width/2,  event.y-self.rect_width*self.height/self.width/2,
                event.x+self.rect_width/2,  event.y+self.rect_width*self.height/self.width/2)


    def zoom_rect(self, event):
        if event.delta < 0:
            self.rect_width = min(self.rect_width*1.15, self.width)
        else:
            self.rect_width = max(self.rect_width/1.15, 3)
        # print(self.rect_width)
        self.new_rectangle(event)

    def zoom_out_draw(self,event):
        x_off, y_off = event.x-self.width/2, self.height/2-event.y
        self.z_center -= complex(real = x_off*self.z_width/self.rect_width , imag = y_off*self.z_width/self.rect_width)
        self.z_width *= self.width/self.rect_width
        changed = (self.iterations, self.color_cycle_speed) != self.control_panel.get_values()[2:4]
        self.iterations, self.color_cycle_speed = self.control_panel.get_values_scale()[2:4]
        self.control_panel.update_values()
        
        self.draw(event, out=True, colors_changed=changed)

    def zoom_in_draw(self,event):
        x_off, y_off = event.x-self.width/2, self.height/2-event.y
        self.z_center += complex(real = x_off*self.z_width/self.width , imag = y_off*self.z_width/self.width)
        self.z_width *= self.rect_width/self.width
        self.iterations, self.color_cycle_speed = self.control_panel.get_values_scale()[2:4]
        self.control_panel.update_values()
        
        self.draw(event)

    def reset_view(self):
        self.z_width, self.z_center, self.iterations = self.default_parameters
        self.draw()

    def get_zoom_level(self):
        return 1/self.z_width

    


import sys
from multiprocessing import freeze_support

if __name__ == '__main__':

    # this is VITAL when creating an .exe file:
    freeze_support()
    # without it, __main__ will get called upon every creation of a new multiprocessing process
    # source: https://stackoverflow.com/a/27694505

    w,h,real_center,imag_center,zoom_level,iterations = 700,700,-0.7,0,1/3,500

    try:
        w = int(sys.argv[1])
        h = int(sys.argv[2])
        real_center = float(sys.argv[3])
        imag_center = float(sys.argv[4])
        zoom_level = float(sys.argv[5])
        iterations = int(sys.argv[6])
    except:
        pass

    import ctypes
    user32 = ctypes.windll.user32
    screensize = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)

    root = tk.Tk()
    if (w,h)==screensize:
        root.attributes('-fullscreen', True)
    else:
        root.geometry(f'{w}x{h}')

    FractalFrame(root,w,h,z_center=complex(real_center,imag_center),zoom_level=zoom_level,iterations=iterations).pack()

    # def keydown(event):
    #     if event.char == 's':
    #         Image.fromarray(numpy.swapaxes(get_image_array(iters=10000,wid=1920*4,hei=1080*4),0,1)).save(f'output/{z_center}_{z_width}.png', 'PNG', optimize=True)


    # root.bind('<KeyPress>', keydown)

    def on_closing():
        root.destroy()
    root.protocol('WM_DELETE_WINDOW', on_closing)

    root.mainloop()


# TODO: Ablity to save image of current view with custom resolution, and custom number of iterations (=accuracy of the image)
# + eventually adding GUI elements that display current zoomlevel and center (make the previous thing a button then)