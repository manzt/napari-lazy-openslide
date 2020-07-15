# napari-lazy-openslide

[![License](https://img.shields.io/pypi/l/napari-lazy-openslide.svg?color=green)](https://github.com/manzt/napari-lazy-openslide/raw/master/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/napari-lazy-openslide.svg?color=green)](https://pypi.org/project/napari-lazy-openslide)
[![Python Version](https://img.shields.io/pypi/pyversions/napari-lazy-openslide.svg?color=green)](https://python.org)
[![tests](https://github.com/manzt/napari-lazy-openslide/workflows/tests/badge.svg)](https://github.com/manzt/napari-lazy-openslide/actions)

An experimental plugin to lazily load multiscale whole-slide tiff images with openslide and dask.

----------------------------------

This [napari] plugin was generated with [Cookiecutter] using with [@napari]'s [cookiecutter-napari-plugin] template.

<!--
Don't miss the full getting started guide to set up your new package:
https://github.com/napari/cookiecutter-napari-plugin#getting-started

and review the napari docs for plugin developers:
https://napari.org/docs/plugins/index.html
-->

## Installation

**Step 1.)** Make sure you have OpenSlide installed. Download instructions [here](https://openslide.org/download/).

**Step 2.)** Install `napari-lazy-openslide` via [pip]:

    pip install napari-lazy-openslide

## Usage

This plugin tries to be conservative with what files it will attempt to provide a reader.
It will only attempt to read `.tif` and `.tiff` files that `openslide` will open and are 
detected as multiscale (`openslide.OpenSlide.level_count > 1`). Under the hood, 
`napari-lazy-openslide` wraps the `openslide` reader with a valid `zarr.Store` where each 
each pyramidal level is exposed as a separate `zarr.Array` with shape `(y,x,4)`.

The plugin is experimental and has only been tested with `CAMELYON16` and `CAMELYON17` datasets, 
which can be downloaded [here](https://camelyon17.grand-challenge.org/Data/).

```bash
$ napari tumor_004.tif
```

![Interactive deep zoom of whole-slide image](tumor_004.gif)

## Contributing

Contributions are very welcome. Tests can be run with [tox], please ensure
the coverage at least stays the same before you submit a pull request.

## License

Distributed under the terms of the [BSD-3] license,
"napari-lazy-openslide" is free and open source software

## Issues

If you encounter any problems, please [file an issue] along with a detailed description.

[napari]: https://github.com/napari/napari
[Cookiecutter]: https://github.com/audreyr/cookiecutter
[@napari]: https://github.com/napari
[MIT]: http://opensource.org/licenses/MIT
[BSD-3]: http://opensource.org/licenses/BSD-3-Clause
[GNU GPL v3.0]: http://www.gnu.org/licenses/gpl-3.0.txt
[GNU LGPL v3.0]: http://www.gnu.org/licenses/lgpl-3.0.txt
[Apache Software License 2.0]: http://www.apache.org/licenses/LICENSE-2.0
[Mozilla Public License 2.0]: https://www.mozilla.org/media/MPL/2.0/index.txt
[cookiecutter-napari-plugin]: https://github.com/napari/cookiecutter-napari-plugin
[file an issue]: https://github.com/manzt/napari-lazy-openslide/issues
[napari]: https://github.com/napari/napari
[tox]: https://tox.readthedocs.io/en/latest/
[pip]: https://pypi.org/project/pip/
[PyPI]: https://pypi.org/
