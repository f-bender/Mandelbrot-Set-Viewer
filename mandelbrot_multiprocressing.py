from multiprocessing.pool import ThreadPool
import time

def foo(bar, baz):
  print (f'hello {bar}')
  time.sleep(10)
  return 'foo' + baz

pool = ThreadPool(processes=1)

async_result = pool.apply_async(foo, ('world', 'foo')) # tuple of args for foo

# do some other stuff in the main process
# while not async_result.ready:
time.sleep(5)

for x in range(1000):
    print(".",end="")
print()

return_val = async_result.get()  # get the return value from your function.
print(return_val)