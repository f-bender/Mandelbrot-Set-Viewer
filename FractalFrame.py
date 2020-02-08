from tkinter import *
from PIL import Image, ImageTk
import numpy
import time
from colormap import Colormap
from mandelbrot_image_multiprocessing import get_image_array
import threading


# TODO: in KLASSE umwandeln, am besten Unterklasse von Frame (oder Panel oder sowas), mit mandelbrot-objekt und Canvas etc als Attribute (self.)

class FractalFrame(Frame):

    def __init__(self,master=None,width=1000, height=1000, iterations=200, color_cycle_speed=5, zoom_level=0.25, z_center=0+0j,
                colormap=Colormap([(255,0,0),(255,255,0),(0,255,0),(0,255,255),(0,0,255),(255,0,255)] ,cyclic=True) ):
        assert width >= 200 and height >= 100 , "Minimum dimensions are 200x100"
        super().__init__(master)
        self.master = master
        self.fractal_image_getter = get_image_array
        self.complete_width = width
        # width of the image (the Frame without the control panel)
        self.width = int(min(0.9*self.complete_width,self.complete_width-100))
        self.height = height
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
        self.control_panel = Frame(self)
        self.control_panel.place(x=self.width, width=self.complete_width-self.width, y=0, height=self.height)

        self.default_view = self.get_image()
        self.default_parameters = (self.z_width, self.z_center, self.iterations)
        self.current_view = self.default_view
        self.redraw()

        self.canvas.bind("<Button-1>", self.zoom_in_draw)
        self.canvas.bind("<Button-3>", self.zoom_out_draw)
        self.canvas.bind("<MouseWheel>", self.zoom_rect)
        self.canvas.bind("<Motion>", self.redraw)
        self.canvas.bind("<Leave>", self.redraw)
        self.master.bind('<Configure>', self.resize)
        # self.master.bind('<ButtonRelease-1>',self.resized_draw)

        self.time_of_resize_drawing = None
        # self.time_of_last_resize = time.time()
        self.thread = threading.Thread(target=self.resized_draw)
        # self.resize_event = None

    def resized_draw(self):
        while True:
            if time.time() > self.time_of_resize_drawing:
                break
        print("drawing")

        self.complete_width = self.master.winfo_width()
        self.width = int(min(0.9*self.complete_width,self.complete_width-100))
        self.height = self.master.winfo_height()

        self.place(x=0,y=0,width=self.complete_width,height=self.height)
        self.canvas.place(x=0,y=0,width=self.width, height=self.height)
        self.control_panel.place(x=self.width,y=0,width=self.complete_width-self.width, height=self.height)

        self.draw()


    def resize(self,event):
        print(event)
        if event.width != self.complete_width or event.height != self.height:
            print("resize event")
            self.time_of_resize_drawing = time.time() + 1
            if not self.thread.is_alive():
                self.thread = threading.Thread(target=self.resized_draw)
                self.thread.start()

        # self.time_of_last_resize = time.time()
        # self.resize_event = event

        # # asyncio.run(self.async_draw())
        # if self.resize_drawing_task:
        #     self.resize_drawing_task.cancel()
        # self.resize_drawing_task = asyncio.create_task(self.async_draw())
        # await self.resize_drawing_task

    # def draw_after_resize(self):
    #     print("in thread")
    #     time.sleep(5)
    #     if time.time()-self.time_of_last_resize >= 5 and self.to_be_configured:
    #         print("drawing")
    #         self.to_be_configured = False

    #         self.complete_width = self.resize_event.width
    #         self.width = int(min(0.9*self.complete_width,self.complete_width-100))
    #         self.height = self.resize_event.height
    #         self.canvas.config(width=self.height, height=self.height)
    #         self.control_panel.config(width=self.complete_width-self.width, height=self.height)

    #         self.draw()

    def get_image(self,width=None, height=None, iterations=None):
        if None in {width, height, iterations}:
            width, height, iterations = self.width, self.height, self.iterations

        start = time.time()
        array = self.fractal_image_getter(width, height, self.z_center, self.z_width, iterations, self.colormap, self.color_cycle_speed)
        print(f"Took {'%.2f' % (time.time()-start)} seconds to load image. Zoomlevel: {self.get_zoom_level()}")
       
        return ImageTk.PhotoImage(Image.fromarray(numpy.swapaxes(array,0,1)))

    def draw(self,event=None):
        self.current_view = self.get_image()
        self.redraw(event)

    def redraw(self,event=None):
        self.canvas.create_image(0,0,image=self.current_view, anchor=NW)
        if event is not None and "Leave event" not in str(event):
            self.canvas.create_rectangle(event.x-self.rect_width/2,  event.y-self.rect_width*self.height/self.width/2, #evtl. x1 statt x0, x2 statt x1 etc
                 event.x+self.rect_width/2,  event.y+self.rect_width*self.height/self.width/2, outline='gray',width=2)

    def zoom_rect(self, event):
        if event.delta < 0:
            self.rect_width *= 1.15
        else:
            self.rect_width /= 1.15
        self.redraw(event)

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
        self.current_view = self.default_view
        self.z_width, self.z_center, self.iterations = self.default_parameters
        self.redraw()

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