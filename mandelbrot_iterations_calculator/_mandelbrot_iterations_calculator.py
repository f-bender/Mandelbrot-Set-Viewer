import numpy as np
from numba import vectorize, cuda


if not cuda.is_available():
    print('No cuda GPU available!')

@vectorize(['int32(float64, float64, int32)'], target='cuda' if cuda.is_available() else 'parallel')
def _get_iters_from_re_im(real, imag, max_iterations):
    """Given the real and imaginary part of a number, returns the number of iterations
       until the absolute value of the number exceeds 2 when following the formula z = z*z + c

    Args:
        real (float): real part of the seed value
        imag (float): imaginary part of the seed value
        iterations (int): maximum number of iterations before the number is considered to never explode

    Returns:
        int: number of iterations until it exceeds 2, or -1 if it never does
    """
    c = complex(real, imag)
    if abs(c) < 0.25:
        return -1
    z = c
    for i in range(max_iterations):
        z = z*z + c
        if abs(z) > 2:
            return i
    return -1


def _get_real_imag_of_view(width, height, z_center, z_width):
    """ Generates matrices containing the complex numbers in a grid of the given width and height.
        The center point of the grid will contain the number `z_center`,
        and the (real) distance between the leftmost column and the rightmost columns will be `z_width`.
        Real and imaginary part of the result are returned as separate matrices.

    Args:
        width (int): width of grid
        height (int): height of grid
        z_center (complex): complex value of center
        z_width (float): difference between leftmost and rightmost real values in result

    Returns:
        tuple(np.array, np.array): real values and imaginary values of the resulting grid
    """

    real = np.empty([width, height], dtype=np.float64)
    real.T[:] = [z_center.real + (x/width - 0.5) * z_width for x in range(width)]

    imag = np.empty([width, height], dtype=np.float64)
    imag[:] = [z_center.imag - (y/width - height/(2*width)) * z_width for y in range(height)]

    return real, imag


def get_iterations_per_pixel(width, height, z_center, z_width, max_iterations, same_position=False, previous_iterations=None):
    if same_position:
        assert previous_iterations is not None

        # for the values outside the mandelbrot set, we already know the number of iterations
        known_idxs = previous_iterations != -1
        unknown_idxs = np.logical_not(known_idxs)

        real, imag = _get_real_imag_of_view(width, height, z_center, z_width)

        # ignore values for which we already know the number of iterations
        real[known_idxs] = imag[known_idxs] = 0

        previous_iterations[unknown_idxs] = _get_iters_from_re_im(real, imag, max_iterations)[unknown_idxs] # pylint: disable=unsupported-assignment-operation
    else:
        real, imag = _get_real_imag_of_view(width, height, z_center, z_width)
        previous_iterations = _get_iters_from_re_im(real, imag, max_iterations)

    return previous_iterations
