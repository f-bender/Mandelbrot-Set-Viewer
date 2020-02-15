import numpy
from colormap import Colormap

from numba import vectorize, cuda

# THIS RUNS IN ANACONDA3 PROMPT (base)

# @vectorize(['int32(float64, float64, int32, float32)'], target='cuda')
# def get_colors_iters_indices(a,b, color_cycle_speed):
#     global colormap
#     c = complex(a,b)
#     z = c
#     for i in range(iterations):
#         z = z*z + c
#         if abs(z) > 10000:
#             i = int(i*color_cycle_speed)
#             return (i%255) if ((i//255) % 2) == 0 else 255-(i%255)
#     return 0

@vectorize(['uint8(float64, float64, int32, float32)'], target='cuda')
def get_colors_from_RE_IM(a,b,iterations, color_cycle_speed):
    global colormap
    c = complex(a,b)
    z = c
    for i in range(iterations):
        z = z*z + c
        if abs(z) > 2:
            i = int(i*color_cycle_speed)
            return i%256 if ((i//255) % 2) == 0 else 255-(i%255)
    return 0

@vectorize(['uint8(float64, float64,int32,float32)'], target='cuda')
def get_iters_from_RE_IM(a,b,iterations,color_cycle_speed):
    c = complex(a,b)
    z = c
    for i in range(iterations):
        z = z*z + c
        if abs(z) > 2:
            i = int(i*color_cycle_speed)
            return i%255
    return 255
# now make two numpy arrays which respectively contain all the real / imaginary parts of the pixels,
# them combine them using this function (just like VectorAdd)
# colormap = Colormap([(255,0,0),(255,255,0),(0,255,0),(0,255,255),(0,0,255),(255,0,255)] ,cyclic=True)
# color_cycle_speed = 5
def get_image_array(w, h,z_center,z_width,iterations,colormap,color_cycle_speed):
    # WORKS!
    real = numpy.empty([w,h],dtype=numpy.float64)
    real.T[:] = [z_center.real + (x/w - 0.5)*z_width for x in range(w)]
    imag = numpy.empty([w,h],dtype=numpy.float64)
    imag[:] = [z_center.imag - (y/w - h/(2*w))*z_width for y in range(h)]

    iters = get_iters_from_RE_IM(real,imag, iterations,color_cycle_speed)
    # print("ti",type(iters))
    # print("is",iters.shape)
    # print(iters)


    sb = numpy.full([w,h],255,dtype=numpy.uint8)
    colors = numpy.dstack((iters,sb,sb))

    # correctly displays values inside the set as black instead of red, but is much slower
    # colors = numpy.empty([w,h,3],dtype=numpy.uint8)
    # for x in range(w):
    #     for y in range(h):
    #         colors[x,y] = [iters[x,y],255,255 if iters[x,y] < 255 else 0]






    # rgb_index = numpy.empty([w,h,3])
    # rgb_index[:] = [0,1,2]

    # colors = get_colors_iters_indices(iters_rgb_index,color_cycle_speed)

    # get_R = lambda x: colormap.get_color(x*color_cycle_speed/600)[0]
    # get_G = lambda x: colormap.get_color(x*color_cycle_speed/600)[1]
    # get_B = lambda x: colormap.get_color(x*color_cycle_speed/600)[2]
    # vgr = numpy.vectorize(get_R)
    # vgg = numpy.vectorize(get_G)
    # vgb = numpy.vectorize(get_B)
    # r, g ,b = vgr(iters),vgg(iters),vgb(iters)
    # colors = numpy.dstack((r,g,b)).astype(numpy.uint8)
    # print(numpy.max(colors), numpy.min(colors))

    # colors = numpy.empty([w,h,3],dtype=numpy.uint8)
    # for x in range(w):
    #     for y in range(h):
    #         colors[x,y] = [iters[x,y]]*3#colormap.get_color(iters[x,y]*color_cycle_speed/600)

    # print("tc",type(colors))
    # print("cs",colors.shape)
    # print(colors)

    # colors = get_colors_from_RE_IM(real,imag,iterations,color_cycle_speed)

    return colors

# def color(iters):
#     global colormap
#     return colormap.get_color(iters*color_cycle_speed/600)



# def write_pixel_new_iters(x,y,w,h,z_center,z_width,iterations,colormap,color_cycle_speed):
#     iters_np = numpy.frombuffer(shared_iters, dtype=numpy.int32).reshape((w,h))
#     # if iters_np[x,y] == -1:
#     actual_iterations = iterations_until_escape(z_center + complex( (x/w - 0.5)*z_width, -(y/w - h/(2*w))*z_width ),iterations)

#     iters_np[x,y] = actual_iterations

#     arr = numpy.frombuffer(shared_colors, dtype=numpy.uint8) # arr and shared_colors share the same memory
#     b = arr.reshape((w,h,3)) # b and arr share the same memory
#     b[x,y] = colormap.get_color(actual_iterations*color_cycle_speed/600)

# def write_pixel_existing_iters(x,y,w,h,z_center,z_width,iterations,colormap,color_cycle_speed, in_ignored_box):
#     iters_np = numpy.frombuffer(shared_iters, dtype=numpy.int32).reshape((w,h))

#     iters = iterations_until_escape(z_center + complex( (x/w - 0.5)*z_width, -(y/w - h/(2*w))*z_width ),iterations) if in_ignored_box else iters_np[x,y]
    
#     arr = numpy.frombuffer(shared_colors, dtype=numpy.uint8) # arr and shared_colors share the same memory
#     b = arr.reshape((w,h,3)) # b and arr share the same memory
#     b[x,y] = colormap.get_color(iters*color_cycle_speed/600)


# def iterations_until_escape(c,iterations):
#     z = c
#     for i in range(iterations):
#         z = z*z + c
#         if abs(z) > 2:
#             return i
#     return -1

# def write_pixel(x,y,w,h,z_center,z_width,iterations,colormap,color_cycle_speed):
#     actual_iterations = iterations_until_escape(z_center + complex( (x/w - 0.5)*z_width, -(y/w - h/(2*w))*z_width ),iterations)

#     # iterations
#     i_arr = numpy.frombuffer(shared_iters, dtype=numpy.int32) # arr and shared_colors share the same memory
#     i_b = i_arr.reshape((w,h)) # b and arr share the same memory
#     i_b[x,y] = actual_iterations

#     # colors
#     arr = numpy.frombuffer(shared_colors, dtype=numpy.uint8) # arr and shared_colors share the same memory
#     b = arr.reshape((w,h,3)) # b and arr share the same memory
#     b[x,y] = colormap.get_color(actual_iterations*color_cycle_speed/600)


