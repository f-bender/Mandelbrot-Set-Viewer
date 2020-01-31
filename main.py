from tkinter import *
from PIL import Image, ImageTk
import numpy
from colormap import Colormap
import time
from mandelbrot import Mandelbrot
from multiprocessing.pool import ThreadPool

threads = 8
pool = ThreadPool(processes=threads)

def foo(bar, baz):
  print (f'hello {bar}')
  time.sleep(10)
  return 'foo' + baz

def get_image_array_multithreaded():

    async_result = pool.apply_async(foo, ('man', 'ngus')) # tuple of args for foo

    # do some other stuff in the main process
    # while not async_result.ready:
    time.sleep(5)

    for _ in range(1000):
        print(".",end="")
    print()

    return_val = async_result.get()  # get the return value from your function.
    print(return_val)



w,h = 800,800
root = Tk()
# root.attributes("-fullscreen", True)
root.geometry(f"{w}x{h}")
canvas = Canvas(root,width=w,height=h)
canvas.pack()
rect_width = 40
wh_ratio = w/h

z_width = 4
z_center = 0+0j

# cmap = Colormap( [(255,0,0),(255,255,0),(0,255,0),(0,255,255),(0,0,255),(255,0,255)] ,cyclic=True)
mandel = Mandelbrot(iterations=200)

sstart = time.time()

# cmap_image = numpy.array([[cmap.get_color((x+y)/h) for x in range(w)] for y in range(h)], dtype=numpy.uint8())
mandelbrot = mandel.get_image_array(z_center,z_width,w,h)
# mandelbrot = get_image_array_multithreaded(z_center,z_width,w,h)

eend = time.time()
print(eend-sstart,"seconds")

# print (cmap_image)


# PIL Images
# adapters for tkinter
# These can be used everywhere Tkinter expects an image object.
# tkinter.Label(root, image=im2, bd=100).grid()

default_view = ImageTk.PhotoImage(Image.fromarray(mandelbrot))
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
    get_image_array_multithreaded()
    end = time.time()
    print(end-start)
    # current_view = ImageTk.PhotoImage(Image.fromarray(new_mandelbrot))
    do_painting(event.x,event.y)
root.bind("<Button-1>", mouse_clicked)

def right_mouse_clicked(event):
    global current_view, z_width, z_center
    x_off, y_off = event.x-w/2, h/2-event.y
    z_center -= complex(x_off*z_width/rect_width ,y_off*z_width/rect_width)
    z_width *= w/rect_width
    start = time.time()
    new_mandelbrot = mandel.get_image_array(z_center,z_width,w,h)
    end = time.time()
    print(end-start)
    current_view = ImageTk.PhotoImage(Image.fromarray(new_mandelbrot))
    do_painting(event.x,event.y)
root.bind("<Button-3>", right_mouse_clicked)

def on_leave(event):
    canvas.create_image(0,0,image=current_view, anchor=NW)
root.bind("<Leave>", on_leave)

root.mainloop()