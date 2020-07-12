"""
This module is a fairly minimal reader for zarr.

It implements the ``napari_get_reader`` hook specification, (to create
a reader plugin) but your plugin may choose to implement any of the hook
specifications offered by napari.
see: https://napari.org/docs/plugins/hook_specifications.html

Replace code below accordingly.  For complete documentation see:
https://napari.org/docs/plugins/for_plugin_developers.html
"""
import numpy as np
from napari_plugin_engine import napari_hook_implementation
from pathlib import Path
from urllib.parse import urlparse
import dask.array as da
import zarr

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
        return None

    if not any(part.endswith('.zarr') for part in Path(path).parts):
        # Don't try to handle if .zarr isn't in path
        return None 
    
    if urlparse(path).scheme not in ("", "file"):
        # TODO: open remote path (S3, GCS) if array ? 
        return None
    
    z = zarr.open(path, mode='r')
    if isinstance(z, zarr.Group):
        if "multiscales" in z.attrs:
            # Don't handle multiscale extension
            return None

    # otherwise we return the *function* that can read ``path``.
    return reader_function


def reader_function(path):
    """Take a path or list of paths and return a list of LayerData tuples.

    Readers are expected to return data as a list of tuples, where each tuple
    is (data, [add_kwargs, [layer_type]]), "add_kwargs" and "layer_type" are
    both optional.

    Parameters
    ----------
    path : str or list of str
        Path to file, or list of paths.

    Returns
    -------
    layer_data : list of tuples
        A list of LayerData tuples where each tuple in the list contains
        (data, metadata, layer_type), where data is a numpy array, metadata is
        a dict of keyword arguments for the corresponding viewer.add_* method
        in napari, and layer_type is a lower-case string naming the type of layer.
        Both "meta", and "layer_type" are optional napari will default to
        layer_type=="image" if not provided
    """
    # Either a group or an array 
    z = zarr.open(path, mode='r')

    if isinstance(z, zarr.Array): 
        add_kwargs = { "name": Path(path).name }
        print(da.from_zarr(z))
        return [(da.from_zarr(z), add_kwargs)]

    # Case where path is a zarr.Group
    layers = []
    for key in sorted(z.array_keys()):
        array = da.from_zarr(z.get(key))
        add_kwargs = { "name": key }
        layers.append((array, add_kwargs))

    return layers






















