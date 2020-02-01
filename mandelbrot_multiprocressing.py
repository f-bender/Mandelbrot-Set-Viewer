from colormap import Colormap
import numpy
import multiprocessing as mp
import warnings
import time
import ctypes as c
import itertools
from mandelbrot_image_multiprocessing import get_image_array_multithreaded



class Mandelbrot:
    def __init__(self, resolution, iterations=200, colormap=Colormap([(255,0,0),(255,255,0),(0,255,0),(0,255,255),(0,0,255),(255,0,255)] ,cyclic=True),
                color_cycle_speed=5, processes=16):
        self.colormap = colormap
        self.iterations = iterations
        self.color_cycle_speed = color_cycle_speed
        self.processes = processes
        self.w, self.h = resolution
        self.image_array = mp.RawArray(c.c_uint8, self.w*self.h*3)
        self.processes = processes
        self.process_pool = mp.Pool(processes=processes, initializer=_init, initargs=(self.image_array,))

    # z_center: complex number,  width: range of numbers on the complex plane that are mapped to the width of the image,  w,h: width, height of image
    def get_image_array(self, z_center, z_width, w=None,h=None,iterations=None):
        if not iterations:
            iterations = self.iterations
        if (w and w != self.w) or (h and h != self.h):
            array = mp.RawArray(c.c_uint8, w*h*3)
            pool = mp.Pool(processes=self.processes, initializer=_init, initargs=(array,))
        else:
            w,h = self.w, self.h
            array = self.image_array
            pool = self.process_pool

        pool.starmap(self.func, (tup+(w,h,z_center,z_width,iterations) for tup in itertools.product(range(w),range(w)) ))

        if w != self.w or h != self.h:
            pool.close()

        return numpy.frombuffer(array, dtype=numpy.uint8()).reshape((w,h,3))

    def close(self):
        self.process_pool.close()

    # # z_center: complex number,  width: range of numbers on the complex plane that are mapped to the width of the image,  w,h: width, height of image
    # def get_image_array(self, z_center, z_width, w,h):
    #     # TODO: Multi threaded
    #     return numpy.array([[  self.colormap.get_color(self.iterations_until_escape(z_center + complex( (x/w - 0.5)*z_width, -(y/w - h/(2*w))*z_width ))*self.color_cycle_speed/self.iterations)   for x in range(w)] for y in range(h)], dtype=numpy.uint8())
    #     # same thing more readable but about 20% less efficient:
    #     # array = numpy.empty((w,h,3), dtype=numpy.uint8())
    #     # for y in range(h):
    #     #     for x in range(w):
    #     #         c = z_center + complex( (x/w - 0.5)*width, -(y/w - h/(2*w))*width)
    #     #         array[y,x] = self.colormap.get_color(self.iterations_until_escape(c)*self.color_cycle_speed/self.iterations)
    #     # return array

    def func(self,x,y,w,h,z_center,z_width,iters):
    #ignore the PEP 3118 buffer warning
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', RuntimeWarning)

            arr = numpy.frombuffer(var_dict["array"], dtype=numpy.uint8()) # arr and shared share the same memory
            # make it three-dimensional
            b = arr.reshape((w,h,3)) # b and arr share the same memory

            b[x,y] = self.colormap.get_color(self.iterations_until_escape(z_center + complex( (x/w - 0.5)*z_width, -(y/w - h/(2*w))*z_width ),iters)*self.color_cycle_speed/600)
