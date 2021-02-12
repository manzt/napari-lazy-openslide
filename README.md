# napari-lazy-openslide

[![License](https://img.shields.io/pypi/l/napari-lazy-openslide.svg?color=green)](https://github.com/manzt/napari-lazy-openslide/raw/master/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/napari-lazy-openslide.svg?color=green)](https://pypi.org/project/napari-lazy-openslide)
[![Python Version](https://img.shields.io/pypi/pyversions/napari-lazy-openslide.svg?color=green)](https://python.org)
[![tests](https://github.com/manzt/napari-lazy-openslide/workflows/tests/badge.svg)](https://github.com/manzt/napari-lazy-openslide/actions)

An experimental plugin to lazily load multiscale whole-slide tiff images with openslide and dask.

----------------------------------

This [napari] plugin was generated with [Cookiecutter] using with [@napari]'s [cookiecutter-napari-plugin] template.

## Installation

**Step 1.)** Make sure you have OpenSlide installed. Download instructions [here](https://openslide.org/download/).

> NOTE: Installation on macOS is easiest via Homebrew: `brew install openslide`. Up-to-date and multiplatform 
> binaries for `openslide` are also avaiable via `conda`: `conda install -c sdvillal openslide-python`

**Step 2.)** Install `napari-lazy-openslide` via `pip`:

    pip install napari-lazy-openslide

## Usage

### Napari plugin

```bash
$ napari tumor_004.tif
```
By installing this package via `pip`, the plugin should be recognized by `napari`. The plugin
attempts to read image formats recognized by `openslide` that are multiscale 
(`openslide.OpenSlide.level_count > 1`). 

It should be noted that `napari-lazy-openslide` is experimental and has primarily 
been tested with `CAMELYON16` and `CAMELYON17` datasets, which can be 
downloaded [here](https://camelyon17.grand-challenge.org/Data/).

![Interactive deep zoom of whole-slide image](tumor_004.gif)


### Using `OpenSlideStore` with Zarr and Dask

The `OpenSlideStore` class wraps an `openslide.OpenSlide` object as a valid Zarr store. 
The underlying `openslide` image pyramid is translated to the Zarr multiscales extension,
where each level of the pyramid is a separate 3D `zarr.Array` with shape `(y, x, 4)`.

```python
import dask.array as da
import zarr

from napari_lazy_openslide import OpenSlideStore

store = OpenSlideStore('tumor_004.tif')
grp = zarr.open(store, mode="r")

# The OpenSlideStore implements the multiscales extension
# https://forum.image.sc/t/multiscale-arrays-v0-1/37930
datasets = grp.attrs["multiscales"][0]["datasets"]

pyramid = [grp.get(d["path"]) for d in datasets]
print(pyramid)
# [
#   <zarr.core.Array '/0' (23705, 29879, 4) uint8 read-only>,
#   <zarr.core.Array '/1' (5926, 7469, 4) uint8 read-only>,
#   <zarr.core.Array '/2' (2963, 3734, 4) uint8 read-only>,
# ]

pyramid = [da.from_zarr(store, component=d["path"]) for d in datasets]
print(pyramid)
# [
#   dask.array<from-zarr, shape=(23705, 29879, 4), dtype=uint8, chunksize=(512, 512, 4), chunktype=numpy.ndarray>,
#   dask.array<from-zarr, shape=(5926, 7469, 4), dtype=uint8, chunksize=(512, 512, 4), chunktype=numpy.ndarray>,
#   dask.array<from-zarr, shape=(2963, 3734, 4), dtype=uint8, chunksize=(512, 512, 4), chunktype=numpy.ndarray>,
# ]

# Now you can use numpy-like indexing with openslide, reading data into memory lazily!
low_res = pyramid[-1][:]
region = pyramid[0][y_start:y_end, x_start:x_end]
```

## Contributing

Contributions are very welcome. Tests can be run with `tox`, please ensure
the coverage at least stays the same before you submit a pull request.

## Issues

If you encounter any problems, please [file an issue] along with a detailed description.

[napari]: https://github.com/napari/napari
[Cookiecutter]: https://github.com/audreyr/cookiecutter
[@napari]: https://github.com/napari
[cookiecutter-napari-plugin]: https://github.com/napari/cookiecutter-napari-plugin
[file an issue]: https://github.com/manzt/napari-lazy-openslide/issues
[PyPI]: https://pypi.org/
