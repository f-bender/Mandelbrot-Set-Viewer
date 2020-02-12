from multiprocessing import Pool, RawArray
import ctypes as c
import itertools
import numpy
import threading
from random import shuffle

def write_pixel_new_iters(x,y,w,h,z_center,z_width,iterations,colormap,color_cycle_speed):
    iters_np = numpy.frombuffer(shared_iters, dtype=numpy.int32).reshape((w,h))
    # if iters_np[x,y] == -1:
    actual_iterations = iterations_until_escape(z_center + complex( (x/w - 0.5)*z_width, -(y/w - h/(2*w))*z_width ),iterations)

    iters_np[x,y] = actual_iterations

    arr = numpy.frombuffer(shared_colors, dtype=numpy.uint8) # arr and shared_colors share the same memory
    b = arr.reshape((w,h,3)) # b and arr share the same memory
    b[x,y] = colormap.get_color(actual_iterations*color_cycle_speed/600)

def write_pixel_existing_iters(x,y,w,h,z_center,z_width,iterations,colormap,color_cycle_speed, in_ignored_box):
    iters_np = numpy.frombuffer(shared_iters, dtype=numpy.int32).reshape((w,h))

    iters = iterations_until_escape(z_center + complex( (x/w - 0.5)*z_width, -(y/w - h/(2*w))*z_width ),iterations) if in_ignored_box else iters_np[x,y]
    
    arr = numpy.frombuffer(shared_colors, dtype=numpy.uint8) # arr and shared_colors share the same memory
    b = arr.reshape((w,h,3)) # b and arr share the same memory
    b[x,y] = colormap.get_color(iters*color_cycle_speed/600)


def iterations_until_escape(c,iterations):
    z = c
    for i in range(iterations):
        z = z*z + c
        if abs(z) > 2:
            return i
    return -1

def write_pixel(x,y,w,h,z_center,z_width,iterations,colormap,color_cycle_speed):
    actual_iterations = iterations_until_escape(z_center + complex( (x/w - 0.5)*z_width, -(y/w - h/(2*w))*z_width ),iterations)

    # iterations
    i_arr = numpy.frombuffer(shared_iters, dtype=numpy.int32) # arr and shared_colors share the same memory
    i_b = i_arr.reshape((w,h)) # b and arr share the same memory
    i_b[x,y] = actual_iterations

    # colors
    arr = numpy.frombuffer(shared_colors, dtype=numpy.uint8) # arr and shared_colors share the same memory
    b = arr.reshape((w,h,3)) # b and arr share the same memory
    b[x,y] = colormap.get_color(actual_iterations*color_cycle_speed/600)



shared_colors = None
shared_iters = None
def _init(colors, iters):
    global shared_colors, shared_iters
    shared_colors, shared_iters =  colors, iters

# def get_image_array(w, h,z_center,z_width,iterations,colormap,color_cycle_speed, processes):
#     temp = RawArray(c.c_uint8, w*h*3)
#     print(processes)
#     pool = Pool(processes=processes, initializer=_init, initargs=(temp,))

#     pool.starmap(write_pixel, (tup+(w,h,z_center,z_width,iterations,colormap,color_cycle_speed) for tup in itertools.product(range(w),range(h))) )

#     pool.close()

#     return numpy.frombuffer(temp, dtype=numpy.uint8()).reshape((w,h,3))

def is_done():
    return not thread.is_alive()


last_parameters = tuple()
thread = None
ignored_box = None

def get_image_array(w, h,z_center,z_width,iterations,colormap,color_cycle_speed, processes, zoom_out_box=None):
    global last_parameters, thread, shared_colors, shared_iters, ignored_box

    if last_parameters and last_parameters[:5] == (w,h,z_center,z_width,iterations):
        last_parameters = (w,h,z_center,z_width,iterations,colormap,color_cycle_speed)
        # global shared_iters

        # colors = RawArray(c.c_uint8, w*h*3)

        thread = threading.Thread(target=colors_from_iters, args=(shared_colors,shared_iters,   w, h,z_center,z_width,iterations,colormap,color_cycle_speed, processes, ignored_box))
        thread.start()

        return numpy.frombuffer(shared_colors, dtype=numpy.uint8).reshape((w,h,3))

        # single processes (slow):
        # iters_np = numpy.frombuffer(shared_iters, dtype=numpy.int32).reshape((w,h))
        # return numpy.array([colormap.get_color(iters_np[x,y]*color_cycle_speed/600) for x in range(w) for y in range(h)],dtype=numpy.uint8).reshape((w,h,3))
    
    elif last_parameters and last_parameters[:4] == (w,h,z_center,z_width) and last_parameters[5:7] == (colormap, color_cycle_speed):
        last_parameters = (w,h,z_center,z_width,iterations,colormap,color_cycle_speed)
        # bei schwarzen neu iterieren, farbige einfach so lassen!
        
        thread = threading.Thread(target=update_iters, args=(shared_colors,shared_iters,   w, h,z_center,z_width,iterations,colormap,color_cycle_speed, processes, ignored_box))
        thread.start()

        return numpy.frombuffer(shared_colors, dtype=numpy.uint8).reshape((w,h,3))


    # elif last_parameters and last_parameters[:4] == (w,h,z_center,z_width):
        # bei schwarzen neu iterieren, bei farbigen nur die Iterationszahl neu interpretieren (diesen Pfad evtl weglassen)
            
    else:
        last_parameters = (w,h,z_center,z_width,iterations,colormap,color_cycle_speed)
        ignored_box = zoom_out_box
        # global thread
        colors, iters = RawArray(c.c_uint8, w*h*3), RawArray(c.c_int32, w*h)
        thread = threading.Thread(target=fill_arrays, args=(colors, iters,  w, h,z_center,z_width,iterations,colormap,color_cycle_speed, processes, zoom_out_box))
        thread.start()

        shared_colors, shared_iters = colors, iters

        return numpy.frombuffer(colors, dtype=numpy.uint8).reshape((w,h,3))


def fill_arrays(color_array, iter_array,   w, h,z_center,z_width,iterations,colormap,color_cycle_speed, processes, ignored_box):
    pool = Pool(processes=processes, initializer=_init, initargs=(color_array,iter_array))

    args = [tup+(w,h,z_center,z_width,iterations,colormap,color_cycle_speed) for tup in itertools.product(range(w),range(h)) if not is_inside(tup[0],tup[1],ignored_box)]
    shuffle(args)
    pool.starmap(write_pixel, args)

    pool.close()

    # return numpy.frombuffer(color_array, dtype=numpy.uint8).reshape((w,h,3))

def colors_from_iters(color_array, iter_array,   w, h,z_center,z_width,iterations,colormap,color_cycle_speed, processes, ignored_box):
    pool = Pool(processes=processes, initializer=_init, initargs=(color_array,iter_array))

    args = [tup+(w,h,z_center,z_width,iterations,colormap,color_cycle_speed,is_inside(tup[0],tup[1],ignored_box)) for tup in itertools.product(range(w),range(h))]
    shuffle(args)
    pool.starmap(write_pixel_existing_iters , args)

    pool.close()

def update_iters(color_array, iter_array,   w, h,z_center,z_width,iterations,colormap,color_cycle_speed, processes, ignored_box):
    pool = Pool(processes=processes, initializer=_init, initargs=(color_array,iter_array))
    iters_np = numpy.frombuffer(shared_iters, dtype=numpy.int32).reshape((w,h))

    args = [tup+(w,h,z_center,z_width,iterations,colormap,color_cycle_speed) for tup in itertools.product(range(w),range(h)) if iters_np[tup[0],tup[1]] == -1 or is_inside(tup[0],tup[1],ignored_box)]
    shuffle(args)
    pool.starmap(write_pixel_new_iters, args)

    pool.close()

def is_inside(x,y,box):
    if box is None:
        return False
    return x >= box[0] and y >= box[1] and x <= box[2] and y <= box[3]