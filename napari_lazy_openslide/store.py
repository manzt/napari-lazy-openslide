from ctypes import ArgumentError
from pathlib import Path
from typing import Any, Dict, Mapping, MutableMapping

import numpy as np
from openslide import OpenSlide
from zarr.storage import _path_to_prefix, attrs_key, init_array, init_group
from zarr.util import json_dumps, normalize_storage_path


def init_attrs(store: MutableMapping, attrs: Mapping[str, Any], path: str = None):
    path = normalize_storage_path(path)
    path = _path_to_prefix(path)
    store[path + attrs_key] = json_dumps(attrs)


def create_meta_store(slide: OpenSlide, tilesize: int) -> Dict[str, bytes]:
    """Creates a dict containing the zarr metadata for the multiscale openslide image."""
    store = dict()
    root_attrs = {
        "multiscales": [
            {
                "name": Path(slide._filename).name,
                "datasets": [{"path": str(i)} for i in range(slide.level_count)],
                "version": "0.1",
            }
        ]
    }
    init_group(store)
    init_attrs(store, root_attrs)
    for i, (x, y) in enumerate(slide.level_dimensions):
        init_array(
            store,
            path=str(i),
            shape=(y, x, 4),
            chunks=(tilesize, tilesize, 4),
            dtype="|u1",
            compressor=None,
        )
    return store


def _parse_chunk_path(path: str):
    """Returns x,y chunk coords and pyramid level from string key"""
    level, ckey = path.split("/")
    y, x, _ = map(int, ckey.split("."))
    return x, y, int(level)


class OpenSlideStore(Mapping):
    """Wraps an OpenSlide object as a multiscale Zarr Store.

    Parameters
    ----------
    path: str
        The file to open with OpenSlide.
    tilesize: int
        Desired "chunk" size for zarr store.
    """

    def __init__(self, path: str, tilesize: int = 512):
        self._slide = OpenSlide(path)
        self._tilesize = tilesize
        self._store = create_meta_store(self._slide, tilesize)

    def __getitem__(self, key: str):
        if key in self._store:
            # key is for metadata
            return self._store[key]

        # key should now be a path to an array chunk
        # e.g '3/4.5.0' -> '<level>/<chunk_key>'
        try:
            x, y, level = _parse_chunk_path(key)
            location = self._ref_pos(x, y, level)
            size = (self._tilesize, self._tilesize)
            tile = self._slide.read_region(location, level, size)
        except ArgumentError as err:
            # Can occur if trying to read a closed slide
            raise err
        except:
            # TODO: probably need better error handling.
            # If anything goes wrong, we just signal the chunk
            # is missing from the store.
            raise KeyError(key)

        return np.array(tile).tobytes()

    def __contains__(self, key: str):
        return key in self._store

    def __eq__(self, other):
        return (
            isinstance(other, OpenSlideStore)
            and self._slide._filename == other._slide._filename
        )

    def __iter__(self):
        return iter(self.keys())

    def __len__(self):
        return sum(1 for _ in self)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def _ref_pos(self, x: int, y: int, level: int):
        dsample = self._slide.level_downsamples[level]
        xref = int(x * dsample * self._tilesize)
        yref = int(y * dsample * self._tilesize)
        return xref, yref

    def keys(self):
        return self._store.keys()

    def close(self):
        self._slide.close()

if __name__ == '__main__':
    import sys
    store = OpenSlideStore(sys.argv[1])
    