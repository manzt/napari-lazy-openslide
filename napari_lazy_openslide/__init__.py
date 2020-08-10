try:
    from ._version import version as __version__
except ImportError:
    __version__ = "unknown"

# replace the asterisk with named imports
from .lazy_openslide import napari_get_reader, OpenSlideStore


__all__ = ["napari_get_reader"]
