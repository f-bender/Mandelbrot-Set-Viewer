# Mandelbrot Set Viewer

An interactive viewer for the Mandelbrot Set using tkinter, hardware accelerated on CPU or cuda-capable GPU using [Numba](https://numba.pydata.org/).

## Installation

Installation is recommended using [Anaconda](https://www.anaconda.com/).  
With Anaconda installed, an environment with all required packages can be created by running

```shell
conda create --name <env-name> --file requirements.txt
```

For GPU support, the lastest [graphics drivers from NVIDIA](https://www.nvidia.com/Download/index.aspx) need to be installed as well.  

In order to run the program, the created environment needs to be activated and the file [`mandelbrot_frame.py`](mandelbrot_frame.py) needs to be executed:

```shell
conda activate <env-name>
python mandelbrot_frame.py
```

If GPU acceleration is **not** available, a corresponding message will be displayed on startup.

## Usage

When moving the mouse over the image, a gray rectangular outline is shown.  
Using the **mouse wheel**, its size can be adjusted.  
By **left-clicking**, the view is zoomed **in** to the area currently framed by this outline.  
By **right-clicking**, the view is zoomed **out** such that the current view ends up inside the outline, *i.e.* it's the inverse of left-clicking.  

The panel on the bottom contains fields for the center, the zoom level, the number of iterations and the speed at which the colors change depending on the number of iterations (Color Cycle Speed).
While zooming in and out by clicking the image, the values for center and zoom level adjust accordingly.  
Alternatively, values can be manually entered into the fields and confirmed by hitting **Enter** to change the view (the number of iterations and the color cycle speed can only be adjusted this way).
A higher number of iterations improves the accuracy of the image, at the cost of performance.
The values can also be adjusted by using the **Arrow Up** and **Arrow Down** keys while the focus is on one of those fields.  

These values can also be specified as command line arguments in order to adjust the initial view after startup.
The window size, or whether to use fullscreen, can also be specified this way.
Resizing the window manually while the program is running is also possible.
For a detailed explanation of the command line arguments, you can run

```shell
python mandelbrot_frame.py --help
```

An image of the current view can be saved using the "Save Image" button on the bottom.
Optionally, a custom resolution and number of iterations can be specified for the image to be saved.  
Center, zoom level and color cycle speed remain the same as in the current view.  
Image names contain the center, zoom level and number of iterations and are saved into the folder [`images/`](images/), which already contains some examples:
| | |
|:-----------------------:|:-----------------------:|
| ![](images/(-0.7515364203184556+0.03318160768869878j)_19700000.0_50000.png) | ![](images/(-0.7528472222222221-0.04321759259259258j)_1121.0_6000.png) |
| ![](images/(-0.7775676807428494+0.12680574494018867j)_54610.0_20000.png) | ![](images/(0.2602083333333333+0.0017438271604938247j)_1120.5931286027546_5000.png) |
