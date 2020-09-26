from pathlib import Path

import numpy as np

import dask.array as da
import zarr
from napari_plugin_engine import napari_hook_implementation
from openslide import PROPERTY_NAME_COMMENT, OpenSlide, OpenSlideUnsupportedFormatError
from zarr.meta import encode_array_metadata, encode_group_metadata
from zarr.storage import array_meta_key, attrs_key, group_meta_key
from zarr.util import json_dumps


def encode_root_attrs(levels):
    datasets = [{"path": str(i)} for i in range(levels)]
    root_attrs = dict(multiscales=[dict(datasets=datasets, version="0.1")])
    return json_dumps(root_attrs)


class OpenSlideStore:
    def __init__(self, path, tilesize=1024, compressor=None):
        self._compressor = compressor
        self._slide = OpenSlide(path)
        self._tilesize = tilesize
        self._store = self._init_store()

    def __getitem__(self, key):
        if key in self._store:
            # ascii encoded json metadata
            return self._store[key]
        # key should now be a path to an array chunk
        # e.g '3/4.5.0' -> '<level>/<chunk_key>'
        try:
            level, chunk_key = key.split("/")
            level = int(level)
            tile = self._slide.read_region(
                location=self._get_reference_pos(chunk_key, level),
                level=level,
                size=(self._tilesize, self._tilesize),
            )
        except:
            raise KeyError
        # convert to numpy array and get underlying bytes
        dbytes = np.array(tile).tobytes()
        if self._compressor:
            # If a zarr compressor is provided, compress the bytes
            # This is completely optional and only useful when
            # remote access to the store is desired.
            return self._compressor.encode(dbytes)
        return dbytes

    def _get_reference_pos(self, chunk_key, level):
        # Don't need channel key, always 0
        y, x, _ = [int(k) for k in chunk_key.split(".")]
        dsample = self._slide.level_downsamples[level]
        xref = int(x * dsample * self._tilesize)
        yref = int(y * dsample * self._tilesize)
        return xref, yref

    def _init_store(self):
        d = dict()
        levels = self._slide.level_count
        # Create group and add multiscale metadata
        d[group_meta_key] = encode_group_metadata()
        d[attrs_key] = encode_root_attrs(levels)
        # Create array metadata for each pyramid level
        base_meta = dict(
            chunks=(self._tilesize, self._tilesize, 4),
            compressor=self._compressor.get_config() if self._compressor else None,
            dtype=np.dtype("uint8"),
            fill_value=0,
            filters=None,
            order="C",
        )
        for level in range(levels):
            xshape, yshape = self._slide.level_dimensions[level]
            arr_key = str(level) + "/" + array_meta_key
            arr_meta = dict(shape=(yshape, xshape, 4), **base_meta)
            d[arr_key] = encode_array_metadata(arr_meta)
        return d

    def keys(self):
        return self._store.keys()

    def __iter__(self):
        return iter(self._store)


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
    z_grp = zarr.open(store, mode="r")
    datasets = z_grp.attrs["multiscales"][0]["datasets"]
    pyramid = [da.from_zarr(store, component=d["path"]) for d in datasets]
    add_kwargs = {"name": Path(path).name}
    return [(pyramid, add_kwargs)]
