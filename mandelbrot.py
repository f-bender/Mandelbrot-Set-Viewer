from colormap import Colormap
import numpy
# import itertools
import threading

class Mandelbrot:
    def __init__(self, iterations=200, colormap=Colormap([(255,0,0),(255,255,0),(0,255,0),(0,255,255),(0,0,255),(255,0,255)] ,cyclic=True),
                color_cycle_speed=5, num_threads=8):
        self.colormap = colormap
        self.iterations = iterations
        self.color_cycle_speed = color_cycle_speed
        self.num_threads = num_threads#[BruteForceThread(n*, x_width, h) for n in range(num_threads)]

    # z_center: complex number,  width: range of numbers on the complex plane that are mapped to the width of the image,  w,h: width, height of image
    def get_image_array(self, z_center, z_width, w,h):
        # TODO: Multi threaded
        return numpy.array([[  self.colormap.get_color(self.iterations_until_escape(z_center + complex( (x/w - 0.5)*z_width, -(y/w - h/(2*w))*z_width ))*self.color_cycle_speed/self.iterations)   for x in range(w)] for y in range(h)], dtype=numpy.uint8())
        # same thing more readable but about 20% less efficient:
        # array = numpy.empty((w,h,3), dtype=numpy.uint8())
        # for y in range(h):
        #     for x in range(w):
        #         c = z_center + complex( (x/w - 0.5)*width, -(y/w - h/(2*w))*width)
        #         array[y,x] = self.colormap.get_color(self.iterations_until_escape(c)*self.color_cycle_speed/self.iterations)
        # return array


    def iterations_until_escape(self,c):
        z = c
        for i in range(self.iterations):
            z = z*z + c
            if abs(z) >= 2:
                return i
        return -1

    def close(self): pass


colormap = Colormap([(255,0,0),(255,255,0),(0,255,0),(0,255,255),(0,0,255),(255,0,255)], cyclic=True)
iterations = 200
color_cycle_speed = 8
num_threads = 32

def get_image_array_multithreaded(z_center, z_width, w,h):
    assert w % num_threads == 0, "Width of Canvas has to be divisible by number of threads"
    array_parts = [numpy.zeros((w//num_threads, h, 3), dtype=numpy.uint8()) for _ in range(num_threads)]
    threads = [BruteForceThread(z_center, z_width, n*w//num_threads, w,h, array_parts[n]) for n in range(num_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    # for a in array_parts:
    #     print(id(a))
    
    return numpy.concatenate(tuple(a for a in array_parts))
    # return array_parts[5]


class BruteForceThread (threading.Thread):
   def __init__(self, z_center, z_width, x_start, w, h, array):
      threading.Thread.__init__(self)
      self.z_center = z_center
      self.z_width = z_width
      self.x_start = x_start
      self.h = h
      self.w = w
      self.array = array
   def run(self):
      get_image_part(self.z_center, self.z_width, self.x_start, self.w, self.h, self.array)

def get_image_part(z_center, z_width, x_start, w, h, array):
    for y in range(h):
        for x in range(x_start, x_start+array.shape[0]):
            c = z_center + complex( (x/w - 0.5)*z_width, -(y/w - h/(2*w))*z_width)
            array[x-x_start,y] = colormap.get_color(iterations_until_escape(c)*color_cycle_speed/iterations)
            

def iterations_until_escape(c):
    z = c
    for i in range(iterations):
        z = z*z + c
        if abs(z) >= 2:
            return i
    return -1
