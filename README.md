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

**Step 2.)** Install `napari-lazy-openslide` via [pip]:

    pip install napari-lazy-openslide

## Usage

This plugin attempts to read image formats recognized by `openslide` that are multiscale 
(`openslide.OpenSlide.level_count > 1`). The `OpenSlideStore` class wraps an `OpenSlide`
object with as a valid Zarr store. The underlying `openslide` image pyramid is translated
to the Zarr multiscales extension, where each level of the pyramid is a separate 3D 
`zarr.Array` with shape `(y, x, 4)`.

The plugin is experimental and has only been tested with `CAMELYON16` and `CAMELYON17` datasets, 
which can be downloaded [here](https://camelyon17.grand-challenge.org/Data/).

```bash
$ napari tumor_004.tif
```

![Interactive deep zoom of whole-slide image](tumor_004.gif)

## Contributing

Contributions are very welcome. Tests can be run with [tox], please ensure
the coverage at least stays the same before you submit a pull request.

## Issues

If you encounter any problems, please [file an issue] along with a detailed description.

[napari]: https://github.com/napari/napari
[Cookiecutter]: https://github.com/audreyr/cookiecutter
[@napari]: https://github.com/napari
[cookiecutter-napari-plugin]: https://github.com/napari/cookiecutter-napari-plugin
[file an issue]: https://github.com/manzt/napari-lazy-openslide/issues
[PyPI]: https://pypi.org/
