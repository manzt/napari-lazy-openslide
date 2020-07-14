"""
This module is an example of a barebones numpy reader plugin for napari.

It implements the ``napari_get_reader`` hook specification, (to create
a reader plugin) but your plugin may choose to implement any of the hook
specifications offered by napari.
see: https://napari.org/docs/plugins/hook_specifications.html

Replace code below accordingly.  For complete documentation see:
https://napari.org/docs/plugins/for_plugin_developers.html
"""
import numpy as np
from napari_plugin_engine import napari_hook_implementation
from openslide import OpenSlide, OpenSlideUnsupportedFormatError, PROPERTY_NAME_COMMENT
import zarr
import dask.array as da
from pathlib import Path

array_meta_key = ".zarray"
group_meta_key = ".zgroup"
group_meta = {"zarr_format": 2}


def create_array_meta(shape, chunks):
    return {
        "chunks": chunks,
        "compressor": None,  # chunk is decoded by openslide, so no zarr compression
        "dtype": "|u1",
        "fill_value": 0.0,
        "filters": None,
        "order": "C",
        "shape": shape,
        "zarr_format": 2,
    }


class OpenSlideStore:
    def __init__(self, path, tilesize=1024):
        self.slide = OpenSlide(path)
        self.tilesize = tilesize

    def __getitem__(self, key):
        if key == group_meta_key:
            return group_meta

        level, rest = key.split("/")
        level = int(level)
        if rest == array_meta_key:
            xshape, yshape = self.slide.level_dimensions[level]
            return create_array_meta(
                shape=(yshape, xshape, 4), chunks=(self.tilesize, self.tilesize, 4)
            )

        tile = self.slide.read_region(
            self._get_reference_pos(rest, level), level, (self.tilesize, self.tilesize),
        )

        return np.array(tile).tobytes()

    def _get_reference_pos(self, chunk_key, level):
        y, x, _ = [int(k) for k in chunk_key.split(".")]
        dsample = self.slide.level_downsamples[level]
        xref = int(x * dsample * self.tilesize)
        yref = int(y * dsample * self.tilesize)
        return xref, yref

    def keys(self):
        yield group_meta_key
        for i in range(self.slide.level_count):
            yield f"{i}/{array_meta_key}"

    def __iter__(self):
        return self.keys()


@napari_hook_implementation
def napari_get_reader(path):
    """A basic implementation of the napari_get_reader hook specification.

    Parameters
    ----------
    path : str or list of str
        Path to file, or list of paths.

    Returns
    -------
    function or None
        If the path is a recognized format, return a function that accepts the
        same path or list of paths, and returns a list of layer data tuples.
    """
    if isinstance(path, list):
        # Don't handle multiple paths
        return None

    # OpenSlide supports many different formats, but I've only tested with multiscale RGBA tiffs.
    if not any(path.endswith(s) for s in (".tif", ".tiff")):
        return None

    try:
        slide = OpenSlide(path)
    except OpenSlideUnsupportedFormatError:
        # if openslide can't open, pass on
        return None

    description = slide.properties.get(PROPERTY_NAME_COMMENT)
    # Don't try to handle OME-TIFF
    # https://github.com/cgohlke/tifffile/blob/b346e3bd7de81de512a6715b01124c8f6d60a707/tifffile/tifffile.py#L5781
    if description and description[-4:] == "OME>":
        return None

    # Don't try to handle tifs that OpenSlide doesn't recognize as multiscale.
    if slide.level_count == 1:
        return None

    slide.close()

    return reader_function


def reader_function(path):
    """Takes a path and returns a LayerData tuple where the data is a dask.array.

    Parameters
    ----------
    path : str
        Path to file

    Returns
    -------
    layer_data : list of LayerData tuples
    """
    store = OpenSlideStore(path)
    pyramid = [da.from_zarr(store, component=k) for k in zarr.open(store).array_keys()]
    add_kwargs = {"name": Path(path).name}
    return [(pyramid, add_kwargs)]
