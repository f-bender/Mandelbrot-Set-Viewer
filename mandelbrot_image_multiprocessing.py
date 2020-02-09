from multiprocessing import Pool, RawArray
import ctypes as c
import itertools
import numpy

def iterations_until_escape(c,iterations):
    z = c
    for i in range(iterations):
        z = z*z + c
        if abs(z) > 2:
            return i
    return -1

def write_pixel(x,y,w,h,z_center,z_width,iterations,colormap,color_cycle_speed):
    arr = numpy.frombuffer(shared, dtype=numpy.uint8()) # arr and shared share the same memory
    b = arr.reshape((w,h,3)) # b and arr share the same memory
    b[x,y] = colormap.get_color(iterations_until_escape(z_center + complex( (x/w - 0.5)*z_width, -(y/w - h/(2*w))*z_width ),iterations)*color_cycle_speed/600)

shared = None
def _init(a):
    global shared
    shared = a

def get_image_array(w, h,z_center,z_width,iterations,colormap,color_cycle_speed, processes):
    temp = RawArray(c.c_uint8, w*h*3)
    print(processes)
    pool = Pool(processes=processes, initializer=_init, initargs=(temp,))

    pool.starmap(write_pixel, (tup+(w,h,z_center,z_width,iterations,colormap,color_cycle_speed) for tup in itertools.product(range(w),range(h))) )

    pool.close()

    return numpy.frombuffer(temp, dtype=numpy.uint8()).reshape((w,h,3))