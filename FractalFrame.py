from tkinter import *
from PIL import Image, ImageTk
import numpy
import time
from colormap import Colormap
from mandelbrot_image_multiprocessing import get_image_array
import threading


# TODO: in KLASSE umwandeln, am besten Unterklasse von Frame (oder Panel oder sowas), mit mandelbrot-objekt und Canvas etc als Attribute (self.)

class FractalFrame(Frame):

    class ControlPanel(Frame):
        def __init__(self, master):
            super().__init__(master)
            self.fractal = master
            Label(self,text="Center:").grid(column=1,row=1)
            Label(self,text="Real Part").grid(column=1,row=2)
            self.real = Entry(self)
            self.real.grid(column=2,row=2,sticky='w')
            # self.real.config(wrap='none')
            Label(self,text="Imaginary Part").grid(column=1,row=3)
            self.imag = Entry(self)
            self.imag.grid(column=2,row=3,sticky='w')

            Label(self,text="Zoomlevel").grid(column=3,row=1)
            self.zoom = Entry(self)
            self.zoom.grid(column=4,row=1,sticky='w')

            Label(self,text="Iterations").grid(column=3,row=2)
            self.iters = Entry(self)
            self.iters.grid(column=4,row=2,sticky='w')

            Label(self,text="Color Cycle Speed").grid(column=3,row=3)
            self.color_cycle_speed = Entry(self)
            self.color_cycle_speed.grid(column=4,row=3,sticky='w')

            self._padx = 10
            self._pady = 10
            self.configure(padx=self._padx,pady=self._pady)

            self.grid_columnconfigure(2,weight=4)
            self.grid_columnconfigure(4,weight=1)

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
            time.sleep(0.01)
            col2_wid = self.grid_bbox(2,0,2,0)[2]//7
            col4_wid = self.grid_bbox(4,0,4,0)[2]//7
            self.real.config(width=col2_wid)
            self.imag.config(width=col2_wid)
            self.zoom.config(width=col4_wid)
            self.iters.config(width=col4_wid)
            self.color_cycle_speed.config(width=col4_wid)


        def get_values(self):
            return (
                complex(float(self.real.get()), float(self.imag.get())),
                1/float(self.zoom.get()),
                int(self.iters.get()),
                float(self.color_cycle_speed.get())
            )





    def __init__(self,master=None,width=1000, height=1000, iterations=200, color_cycle_speed=5, zoom_level=0.25, z_center=0+0j,
                colormap=Colormap([(255,0,0),(255,255,0),(0,255,0),(0,255,255),(0,0,255),(255,0,255)] ,cyclic=True) ):
        assert width >= 200 and height >= 100 , "Minimum dimensions are 200x100"
        super().__init__(master)
        self.master = master
        self.fractal_image_getter = get_image_array
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

        self.time_of_resize_drawing = None
        # self.time_of_last_resize = time.time()
        self.thread = threading.Thread(target=self.resized_draw)
        # self.resize_event = None

    def update_values(self,event):
        self.z_center, self.z_width, self.iterations, self.color_cycle_speed = self.control_panel.get_values()
        self.draw()

    def resized_draw(self):
        while True:
            if time.time() > self.time_of_resize_drawing:
                break

        self.complete_height = self.master.winfo_height()
        # self.height = int(min(0.9*self.complete_height,self.complete_height-100))
        self.height = self.complete_height-self.control_panel.get_required_height()
        self.width = self.master.winfo_width()

        self.place(x=0,y=0,width=self.width,height=self.complete_height)
        self.canvas.place(x=0,y=0,width=self.width, height=self.height)
        self.control_panel.place(x=0, width=self.width, y=self.height, height=self.control_panel.get_required_height())

        self.control_panel.resize()

        self.draw()

    def resize(self,event):
        if event.width != self.width or event.height != self.complete_height:
            self.time_of_resize_drawing = time.time() + 1
            if not self.thread.is_alive():
                self.thread = threading.Thread(target=self.resized_draw)
                self.thread.start()

    def get_image(self,width=None, height=None, iterations=None):
        if None in {width, height, iterations}:
            width, height, iterations = self.width, self.height, self.iterations

        start = time.time()
        array = self.fractal_image_getter(width, height, self.z_center, self.z_width, iterations, self.colormap, self.color_cycle_speed)
        print(f"Took {'%.2f' % (time.time()-start)} seconds to load image. Zoomlevel: {self.get_zoom_level()}")
       
        return ImageTk.PhotoImage(Image.fromarray(numpy.swapaxes(array,0,1)))

    def draw(self,event=None):
        old_view = self.current_view
        self.image = self.get_image()
        self.current_view = self.canvas.create_image(0,0,image=self.image, anchor=NW)
        self.canvas.tag_raise(self.rectangle)
        self.control_panel.update_values()
        if old_view is not None:
            self.canvas.delete(old_view)
        self.new_rectangle(event)

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
            self.rectangle = self.canvas.create_rectangle(event.x-self.rect_width/2,  event.y-self.rect_width*self.height/self.width/2,
                                event.x+self.rect_width/2,  event.y+self.rect_width*self.height/self.width/2, outline='gray',width=2)

            # why this is necessary: https://stackoverflow.com/questions/46060570/tkinter-the-shape-isnt-uniform-and-the-animation-looks-bad
            # especially https://stackoverflow.com/a/54954035 explains it well
            self.canvas.configure(bg="grey")


    def zoom_rect(self, event):
        if event.delta < 0:
            self.rect_width *= 1.15
        else:
            self.rect_width /= 1.15
        print(self.rect_width)
        self.new_rectangle(event)

    def zoom_out_draw(self,event):
        x_off, y_off = event.x-self.width/2, self.height/2-event.y
        self.z_center -= complex(real = x_off*self.z_width/self.rect_width , imag = y_off*self.z_width/self.rect_width)
        self.z_width *= self.width/self.rect_width
        
        self.draw(event)

    def zoom_in_draw(self,event):
        x_off, y_off = event.x-self.width/2, self.height/2-event.y
        self.z_center += complex(real = x_off*self.z_width/self.width , imag = y_off*self.z_width/self.width)
        self.z_width *= self.rect_width/self.width
        
        self.draw(event)

    def reset_view(self):
        self.z_width, self.z_center, self.iterations = self.default_parameters
        self.draw()

    def get_zoom_level(self):
        return 1/self.z_width

    




if __name__ == '__main__':
    w,h = 600,600

    root = Tk()
    if (w,h)==(1920,1080):
        root.attributes("-fullscreen", True)
    else:
        root.geometry(f"{w}x{h}")

    FractalFrame(root,w,h).pack()

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