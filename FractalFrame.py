from tkinter import *
from PIL import Image, ImageTk
import numpy
import time
from colormap import Colormap
import mandelbrot_image_cuda as image_creator
import threading
from math import ceil

CHAR_WIDTH = 8
Z_CENTER_DIGITS = 22

class FractalFrame(Frame):

    class ControlPanel(Frame):
        def __init__(self, master):
            super().__init__(master)
            self.fractal = master
            Label(self,text="Center:").grid(column=1,row=1)
            Label(self,text="Real Part").grid(column=1,row=2)
            self.real = Entry(self,width=Z_CENTER_DIGITS)
            self.real.grid(column=2,row=2,sticky='w')
            # self.real.config(wrap='none')
            Label(self,text="Imaginary Part").grid(column=1,row=3)
            self.imag = Entry(self,width=Z_CENTER_DIGITS)
            self.imag.grid(column=2,row=3,sticky='w')

            Label(self,text="Zoomlevel").grid(column=3,row=1)
            self.zoom = Entry(self,width=10)
            self.zoom.grid(column=4,row=1,sticky='w')

            Label(self,text="Iterations").grid(column=3,row=2)
            self.iters = Entry(self,width=10)
            self.iters.grid(column=4,row=2,sticky='w')

            Label(self,text="Color Cycle Speed").grid(column=3,row=3)
            self.color_cycle_speed = Entry(self,width=10)
            self.color_cycle_speed.grid(column=4,row=3,sticky='w')

            self._padx = 10
            self._pady = 10
            self.configure(padx=self._padx,pady=self._pady)

            # self.grid_columnconfigure(2,weight=4)
            # self.grid_columnconfigure(4,weight=1)

            self.real.bind('<Return>',self.master.update_values)
            self.imag.bind('<Return>',self.master.update_values)
            self.zoom.bind('<Return>',self.master.update_values)
            self.iters.bind('<Return>',self.master.update_values)
            self.color_cycle_speed.bind('<Return>',self.master.update_values)

            self.update_values()

        def get_required_height(self):
            return self.grid_bbox()[3] + 2*self._pady

        def update_values(self):
            self.real.delete(0,END)
            self.imag.delete(0,END)
            self.zoom.delete(0,END)
            self.iters.delete(0,END)
            self.color_cycle_speed.delete(0,END)

            self.real.insert(END,self.fractal.z_center.real)
            self.imag.insert(END,self.fractal.z_center.imag)
            self.zoom.insert(END,'%.4g' % self.fractal.get_zoom_level())
            self.iters.insert(END,self.fractal.iterations)
            self.color_cycle_speed.insert(END,self.fractal.color_cycle_speed)
        
        def resize(self):
            # time.sleep(0.01)
            self.real.config(width=Z_CENTER_DIGITS)
            self.imag.config(width=Z_CENTER_DIGITS)
            self.zoom.config(width=10)
            self.iters.config(width=10)
            self.color_cycle_speed.config(width=10)
            if self.grid_bbox()[2] > self.winfo_width():
                rest_width = self.winfo_width() - self.grid_bbox(1,0,1,0)[2] - self.grid_bbox(3,0,3,0)[2]
                entry_width = int(rest_width/2/CHAR_WIDTH)
                self.real.config(width=entry_width)
                self.imag.config(width=entry_width)
                self.zoom.config(width=entry_width)
                self.iters.config(width=entry_width)
                self.color_cycle_speed.config(width=entry_width)


        def get_values(self):
            return (
                complex(float(self.real.get()), float(self.imag.get())),
                1/float(self.zoom.get()),
                int(self.iters.get()),
                float(self.color_cycle_speed.get())
            )





    def __init__(self,master=None,width=1000, height=1000, iterations=200, color_cycle_speed=5, zoom_level=0.25, z_center=0+0j,
                colormap=Colormap([(255,0,0),(255,255,0),(0,255,0),(0,255,255),(0,0,255),(255,0,255)] ,cyclic=True), processes=None, fluid_animation=False):
        assert width >= 300 and height >= 200 , "Minimum dimensions are 300x200"
        super().__init__(master)
        if processes is None:
            self.processes = 1
        else:
            self.processes = processes
        self.fluid_animation = fluid_animation
        self.master = master
        # self.fractal_image_getter = get_image_array
        self.complete_height = height
        # height of the image (the Frame without the control panel)
        self.height = int(min(0.9*self.complete_height,self.complete_height-100))
        self.width = width
        self.colormap = colormap
        self.iterations = iterations
        self.color_cycle_speed = color_cycle_speed
        self.canvas = Canvas(self, width=width, height=height)
        # Label(self, text = 'Length:').grid(row = 1, column = 2)
        self.canvas.pack()
        self.z_width = 1/zoom_level
        self.z_center = z_center
        self.rect_width = width/10
        # Control Panel: a frame on the right side of this FractalFrame, to have some direct 
        # control over and display of the parameters (e.g. zoom_level, z-center, iterations)
        self.control_panel = self.ControlPanel(self)
        self.control_panel.place(x=0, width=self.width, y=self.height, height=self.complete_height-self.height)

        self.image = None
        self.cropped = None
        

        self.default_parameters = (self.z_width, self.z_center, self.iterations)

        self.rectangle = self.canvas.create_rectangle(-self.rect_width, -self.rect_width*self.height/self.width,0,0, outline='gray',width=2)
        self.current_view = None
        # self.draw()

        self.canvas.bind("<Button-1>", self.zoom_in_draw)
        self.canvas.bind("<Button-3>", self.zoom_out_draw)
        self.canvas.bind("<MouseWheel>", self.zoom_rect)
        self.canvas.bind("<Motion>", self.new_rectangle)
        self.canvas.bind("<Leave>", self.new_rectangle)
        self.master.bind('<Configure>', self.resize)

        self.time_of_resize_drawing = time.time()
        # self.time_of_last_resize = time.time()
        self.resize_thread = threading.Thread(target=self.resized_draw,args=(True,))
        self.refresh_thread = None
        # self.resize_event = None
        self.resize_thread.start()

    def update_values(self,event):
        if self.refresh_thread is None or not self.refresh_thread.is_alive():
            same_pos = False
            if self.z_center == self.control_panel.get_values()[0] and self.control_panel.get_values()[1] == 1/float('%.4g' % self.get_zoom_level()):
                same_pos = True
            self.z_center, self.z_width, self.iterations, self.color_cycle_speed = self.control_panel.get_values()
            self.draw(same_pos=same_pos)

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

            zoom_out_box = self.get_rect_coords(event) if out and not colors_changed else None

            start = time.time()
            array = image_creator.get_image_array(width, height, self.z_center, 1/float('%.4g' % self.get_zoom_level()), iterations, self.colormap, self.color_cycle_speed)#, self.processes, zoom_out_box)
            # TODO: do this with an async Coroutine (something like JS's setInterval() instead of time.sleep()?) to prevent flickering!
            # self.refresh_thread = threading.Thread(target=self.redraw, args=(start,numpy.swapaxes(array,0,1),event, same_pos, out, colors_changed))
            # self.refresh_thread.start() # <- without cuda
            
            # <cuda stuff>
            print(time.time()-start,"seconds")
            old_view = self.current_view
            self.image = ImageTk.PhotoImage(Image.fromarray(numpy.swapaxes(array,0,1),mode='HSV'))
            self.current_view = self.canvas.create_image(0,0,image=self.image, anchor=NW)
            if old_view is not None:
                    self.canvas.delete(old_view) 
            self.canvas.tag_raise(self.rectangle)
            # </cuda stuff>



        # old_view = self.current_view
        # self.image = self.get_image()
        # self.current_view = self.canvas.create_image(0,0,image=self.image, anchor=NW)
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
            self.current_view = self.canvas.create_image(0,0,image=self.photo_image, anchor=NW)
            if old_view is not None:
                    self.canvas.delete(old_view) 
            self.canvas.tag_raise(self.rectangle)

            # print(f"Took {'%.5f' % (time.time()-t)} for cycle") 

        old_view = self.current_view
        self.image = Image.fromarray(array)
        if out and not colors_changed:
            assert self.cropped is not None, "cropped is None while zooming out!"
            mask = self.image.convert('L')              # make it grayscale
            mask = mask.point(lambda p: p > 0 and 255)  # make all pixels with values above 0 white
            self.image = Image.composite(self.image, self.cropped, mask)

        self.photo_image = ImageTk.PhotoImage(self.image)
        self.current_view = self.canvas.create_image(0,0,image=self.photo_image, anchor=NW)
        if old_view is not None:
                self.canvas.delete(old_view) 
        self.canvas.tag_raise(self.rectangle)
        
        es = "es"
        s = ""
        print(f"Took {'%.2f' % (time.time()-start)} seconds to load image. ({self.processes} process{es if self.processes > 1 else s})")


    # def redraw(self,event=None):
    #     # self.view = self.canvas.create_image(0,0,image=self.current_view, anchor=NW)
    #     if event is not None and "Leave event" not in str(event):
    #         # self.canvas.create_rectangle(event.x-self.rect_width/2,  event.y-self.rect_width*self.height/self.width/2,
    #         #      event.x+self.rect_width/2,  event.y+self.rect_width*self.height/self.width/2, outline='gray',width=2)
    #         self.canvas.coords(self.rectangle,(event.x-self.rect_width/2,  event.y-self.rect_width*self.height/self.width/2,
    #              event.x+self.rect_width/2,  event.y+self.rect_width*self.height/self.width/2))
    #         # self.canvas.move(self.rectangle, event.x-x, event.y-y)

    def new_rectangle(self,event):
        self.canvas.delete(self.rectangle)
        if event is not None and "Leave event" not in str(event):
            coords = self.get_rect_coords(event)
            self.rectangle = self.canvas.create_rectangle(coords[0],coords[1],coords[2],coords[3], outline='gray',width=2)

            # why this is necessary: https://stackoverflow.com/questions/46060570/tkinter-the-shape-isnt-uniform-and-the-animation-looks-bad
            # especially https://stackoverflow.com/a/54954035 explains it well
            self.canvas.configure(bg="black")

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
        self.iterations, self.color_cycle_speed = self.control_panel.get_values()[2:4]
        self.control_panel.update_values()
        
        self.draw(event, out=True, colors_changed=changed)

    def zoom_in_draw(self,event):
        x_off, y_off = event.x-self.width/2, self.height/2-event.y
        self.z_center += complex(real = x_off*self.z_width/self.width , imag = y_off*self.z_width/self.width)
        self.z_width *= self.rect_width/self.width
        self.iterations, self.color_cycle_speed = self.control_panel.get_values()[2:4]
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

    processes,w,h = None,600,600

    try:
        processes = int(sys.argv[1])
        w = int(sys.argv[2])
        h = int(sys.argv[3])
    except:
        pass

    root = Tk()
    if (w,h)==(1920,1080):
        root.attributes("-fullscreen", True)
    else:
        root.geometry(f"{w}x{h}")

    FractalFrame(root,w,h,processes=processes).pack()

    # def keydown(event):
    #     if event.char == 's':
    #         Image.fromarray(numpy.swapaxes(get_image_array(iters=10000,wid=1920*4,hei=1080*4),0,1)).save(f"output/{z_center}_{z_width}.png", "PNG", optimize=True)


    # root.bind("<KeyPress>", keydown)

    def on_closing():
        root.destroy()
    root.protocol("WM_DELETE_WINDOW", on_closing)

    root.mainloop()


# TODO: Ablity to save image of current view with custom resolution, and custom number of iterations (=accuracy of the image)
# + eventually adding GUI elements that display current zoomlevel and center (make the previous thing a button then)