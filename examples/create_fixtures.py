import numpy as np
import zarr
from skimage import data
from napari_zarr_io import napari_get_reader

pixels = data.astronaut()

# Simple RGB image (Y,X,C)
rgb = zarr.open(
    "rgb_astronaut.zarr", dtype=pixels.dtype, shape=pixels.shape, chunks=(None, None, 3)
)
rgb[:] = pixels

# RGB image split into different channel arrays
red = pixels[:, :, 0]
green = pixels[:, :, 1]
blue = pixels[:, :, 2]

grp = zarr.open_group("channels_astronaut.zarr")
grp.create_dataset("red", data=red)
grp.create_dataset("green", data=green)
grp.create_dataset("blue", data=blue)
