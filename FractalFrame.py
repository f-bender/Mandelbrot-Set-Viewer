from tkinter import *
from PIL import Image, ImageTk
import numpy
from colormap import Colormap
import time
from mandelbrot import Mandelbrot
import multiprocessing as mp
import warnings
import time
from colormap import Colormap
import ctypes as c
import itertools


# TODO: in KLASSE umwandeln, am besten Unterklasse von Frame (oder Panel oder sowas), mit mandelbrot-objekt und Canvas etc als Attribute (self.)

class FractalFrame(Frame):

    def __init__(self,fractal=Mandelbrot(),width=1000, height=1000,
                colormap=Colormap([(255,0,0),(255,255,0),(0,255,0),(0,255,255),(0,0,255),(255,0,255)] ,cyclic=True) ):
        self.fractal = fractal
        self.width = width
        self.height = height
        self.colormap = colormap

cmap = Colormap([(255,0,0),(255,255,0),(0,255,0),(0,255,255),(0,0,255),(255,0,255)] ,cyclic=True)
iterations = 600
color_cycle_speed = 5

def get_color(x,y,w,h,z_center,z_width,iters):
    # iters = iterations_until_escape( z_center + complex( (x/w - 0.5)*z_width, -(y/w - h/(2*w))*z_width ) )
    # if iters == -1:
    #     return (0,0,0)
    # return (255-iters,255-iters,255-iters)
    return cmap.get_color(iterations_until_escape(z_center + complex( (x/w - 0.5)*z_width, -(y/w - h/(2*w))*z_width ),iters)/120)


def iterations_until_escape(c,iters):
    z = c
    for i in range(iters):
        z = z*z + c
        if abs(z) >= 2:
            return i
    return -1




def func(x,y,w,h,z_center,z_width,iters):
    #ignore the PEP 3118 buffer warning
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', RuntimeWarning)
        # w,h = 800,800

        arr = numpy.frombuffer(shared.get_obj(), dtype=numpy.uint8()) # arr and shared share the same memory
        # make it three-dimensional
        b = arr.reshape((w,h,3)) # b and arr share the same memory

        b[x,y] = get_color(x,y,w,h,z_center,z_width,iters)
        # b[ (n//(h*3)) % w, (n//3) % h ] = (n,n+1,n+2)

shared = None
def _init(a):
    global shared
    shared = a

def get_image_array_multithreaded(iters, wid, hei):

    # !!! Consider partly rolling back to the last version on GitHub

    # a = mp.Array(c.c_uint8, w*h*3)
    # temporary = False
    # if wid*hei*3 != len(a):
    temp = mp.Array(c.c_uint8, wid*hei*3)
        # temporary = True
    pool = mp.Pool(processes=16, initializer=_init, initargs=(temp,))
    # else:
    #     a = mp.Array(c.c_uint8, w*h*3)
    #     pool = mp.Pool(processes=10, initializer=_init, initargs=(a,))

    pool.starmap(func, (tup+(wid,hei,z_center,z_width,iters) for tup in itertools.product(range(wid),range(hei)) ))
    # pool.starmap(func, zip(range(0,w*h*3,3), (w for _ in range(w*h)), (w for _ in range(w*h)), [processes]*w*h)) # seemingly worse performance
    
    # pool.close()
    # if temporary:
    return numpy.frombuffer(temp.get_obj(), dtype=numpy.uint8()).reshape((wid,hei,3))
    # b = numpy.frombuffer(a.get_obj(), dtype=numpy.uint8()).reshape((wid,hei,3))
    # return b


if __name__ == '__main__':
    w,h = 800,800
    processes = 16

    # print(list(zip(range(0,w*h*3,3),[w]*w*h,[h]*w*h))
    
    a = mp.Array(c.c_uint8, w*h*3)
    pool = mp.Pool(processes=processes, initializer=_init, initargs=(a,))
    
    root = Tk()
    if (w,h)==(1920,1080):
        root.attributes("-fullscreen", True)
    else:
        root.geometry(f"{w}x{h}")
    canvas = Canvas(root,width=w,height=h)
    canvas.pack()
    rect_width = 40
    wh_ratio = w/h

    z_width = 4
    z_center = 0+0j

    # cmap = Colormap( [(255,0,0),(255,255,0),(0,255,0),(0,255,255),(0,0,255),(255,0,255)] ,cyclic=True)
    # mandel = Mandelbrot(iterations=200)

    sstart = time.time()

    # cmap_image = numpy.array([[cmap.get_color((x+y)/h) for x in range(w)] for y in range(h)], dtype=numpy.uint8())
    # mandelbrot = mandel.get_image_array(z_center,z_width,w,h)
    mandelbrot = get_image_array_multithreaded(iters=iterations, wid=w, hei=h)

    eend = time.time()
    print(eend-sstart,"seconds")

    # print (cmap_image)


    # PIL Images
    # adapters for tkinter
    # These can be used everywhere Tkinter expects an image object.
    # tkinter.Label(root, image=im2, bd=100).grid()

    default_view = ImageTk.PhotoImage(Image.fromarray(numpy.swapaxes(mandelbrot,0,1)))
    current_view = default_view
    canvas.create_image(0,0,image=current_view, anchor=NW)

    def do_painting(x,y):
        canvas.create_image(0,0,image=current_view, anchor=NW)
        canvas.create_rectangle(x-rect_width/2,y-rect_width/wh_ratio/2, x+rect_width/2, y+rect_width/wh_ratio/2, outline='gray',width=2)

    def motion(event):
        do_painting(event.x, event.y)
    root.bind('<Motion>', motion)

    def mouse_wheel(event):
        global rect_width
        if event.delta < 0:
            rect_width *= 1.15
        else:
            rect_width /= 1.15
        do_painting(event.x,event.y)
    root.bind("<MouseWheel>", mouse_wheel)

    def mouse_clicked(event):
        global current_view, z_width, z_center
        x_off, y_off = event.x-w/2, h/2-event.y
        z_center += complex(x_off*z_width/w ,y_off*z_width/w)
        z_width *= rect_width/w
        start = time.time()
        # new_mandelbrot = mandel.get_image_array(z_center,z_width,w,h)
        new_mandelbrot = get_image_array_multithreaded(iters=iterations, wid=w, hei=h)
        end = time.time()
        print(end-start)
        current_view = ImageTk.PhotoImage(Image.fromarray(numpy.swapaxes(new_mandelbrot,0,1)))
        do_painting(event.x,event.y)
    root.bind("<Button-1>", mouse_clicked)

    def right_mouse_clicked(event):
        global current_view, z_width, z_center
        x_off, y_off = event.x-w/2, h/2-event.y
        z_center -= complex(x_off*z_width/rect_width ,y_off*z_width/rect_width)
        z_width *= w/rect_width
        start = time.time()
        # new_mandelbrot = mandel.get_image_array(z_center,z_width,w,h)
        new_mandelbrot = get_image_array_multithreaded(iters=iterations, wid=w, hei=h)
        end = time.time()
        print(end-start)
        current_view = ImageTk.PhotoImage(Image.fromarray(numpy.swapaxes(new_mandelbrot,0,1)))
        do_painting(event.x,event.y)
    root.bind("<Button-3>", right_mouse_clicked)

    def on_leave(event):
        canvas.create_image(0,0,image=current_view, anchor=NW)
    root.bind("<Leave>", on_leave)

    def keydown(event):
        if event.char == 's':
            Image.fromarray(numpy.swapaxes(get_image_array_multithreaded(iters=10000,wid=1920*4,hei=1080*4),0,1)).save(f"output/{z_center}_{z_width}.png", "PNG", optimize=True)


    root.bind("<KeyPress>", keydown)

    def on_closing():
        pool.close()
        root.destroy()
    root.protocol("WM_DELETE_WINDOW", on_closing)

    root.mainloop()


# TODO: Ablity to save image of current view with custom resolution, and custom number of iterations (=accuracy of the image)
# + eventually adding GUI elements that display current zoomlevel and center (make the previous thing a button then)