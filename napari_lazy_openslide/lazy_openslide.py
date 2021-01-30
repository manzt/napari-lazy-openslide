import dask.array as da
import zarr
from napari_plugin_engine import napari_hook_implementation
from openslide import PROPERTY_NAME_COMMENT, OpenSlide, OpenSlideUnsupportedFormatError

from .store import OpenSlideStore


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

    if OpenSlide.detect_format(path) is None:
        return None

    try:
        slide = OpenSlide(path)
    except OpenSlideUnsupportedFormatError:
        return None

    description = slide.properties.get(PROPERTY_NAME_COMMENT)
    # Don't try to handle OME-TIFF
    # https://github.com/cgohlke/tifffile/blob/b346e3bd7de81de512a6715b01124c8f6d60a707/tifffile/tifffile.py#L5781
    if description and description[-4:] == "OME>":
        return None

    # Don't try to handle files that aren't multiscale.
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
    grp = zarr.open(store, mode="r")

    multiscales = grp.attrs["multiscales"][0]
    pyramid = [
        da.from_zarr(store, component=d["path"]) for d in multiscales["datasets"]
    ]
    add_kwargs = {"name": multiscales["name"]}
    return [(pyramid, add_kwargs)]
