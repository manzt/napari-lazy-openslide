import numpy as np
from napari_plugin_engine import napari_hook_implementation
from openslide import OpenSlide, OpenSlideUnsupportedFormatError, PROPERTY_NAME_COMMENT
import zarr
from zarr.util import json_dumps
import dask.array as da
from pathlib import Path

ZARR_FORMAT = 2
ZARR_META_KEY = ".zattrs"
ZARR_ARRAY_META_KEY = ".zarray"
ZARR_GROUP_META_KEY = ".zgroup"
ZARR_GROUP_META = {"zarr_format": ZARR_FORMAT}


def create_array_meta(shape, chunks, compressor):
    return {
        "chunks": chunks,
        "compressor": compressor.get_config()
        if compressor
        else None,  # chunk is decoded by openslide, so no zarr compression
        "dtype": "|u1",  # RGB/A images only
        "fill_value": 0.0,
        "filters": None,
        "order": "C",
        "shape": shape,
        "zarr_format": ZARR_FORMAT,
    }


def create_root_attrs(levels):
    datasets = [{"path": str(i)} for i in range(levels)]
    return {"multiscales": [{"datasets": datasets, "version": "0.1"}]}


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
        d[ZARR_GROUP_META_KEY] = json_dumps(ZARR_GROUP_META)
        d[ZARR_META_KEY] = json_dumps(create_root_attrs(levels))
        # Create array metadata for each pyramid level
        for level in range(levels):
            xshape, yshape = self._slide.level_dimensions[level]
            array_meta = create_array_meta(
                shape=(yshape, xshape, 4),
                chunks=(self._tilesize, self._tilesize, 4),
                compressor=self._compressor,
            )
            d[f"{level}/{ZARR_ARRAY_META_KEY}"] = json_dumps(array_meta)
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
