import multiprocessing as mp
import numpy as np
import warnings
import time
import ctypes as c

w,h = 2,3

def func(n):
    #ignore the PEP 3118 buffer warning
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', RuntimeWarning)
        
        # v = np.ctypeslib.as_array(shared)
        # # if n == 3:
        # time.sleep(1)
        # v[n] = n
        # print(type(shared.get_obj()))
        arr = np.frombuffer(shared.get_obj(), dtype=np.uint8()) # arr and shared share the same memory
        # make it three-dimensional
        b = arr.reshape((w,h,3)) # b and arr share the same memory
        print( (n//(h*3)) % w, (n//3) % h, n%3, n)
        b[ (n//(h*3)) % w, (n//3) % h ] = (n,n+1,n+2)


    # print(n, v)
    # return v.ctypes.data  #return the address

shared = None
def _init(a):
    global shared
    shared = a

if __name__ == '__main__':
    
    # tmp = np.ctypeslib.as_ctypes(np.zeros((5),dtype=np.uint8()))
    # a = mp.sharedctypes.Array(tmp._type_, tmp, lock=False) # lock=False unproblematic because every value only ever gets set by one of the processes
    a = mp.Array(c.c_uint8, w*h*3)

    pool = mp.Pool(processes=10, initializer=_init, initargs=(a,))

    now = time.time()
    pool.map(func, range(0,w*h*3,3))
    print(time.time()-now)
    pool.close()

    b = np.frombuffer(a.get_obj(), dtype=np.uint8()).reshape((w,h,3))
    print(b)