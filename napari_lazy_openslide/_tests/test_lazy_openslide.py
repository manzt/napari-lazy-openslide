import numpy as np
from napari_lazy_openslide import napari_get_reader
from pathlib import Path

fixture_dir = Path.cwd() / ".." / ".." / "fixtures"

# tmp_path is a pytest fixture
def test_reader(tmp_path):
    """An example of how you might test your plugin."""
    # TODO: create sample fixture
    # np.testing.assert_allclose(original_data, layer_data_tuple[0])


def test_get_reader_pass():
    assert napari_get_reader("fake.file") is None
    assert napari_get_reader(["d0.tif", "d1.tif"]) is None
    assert napari_get_reader(str(fixture_dir / "dataset.ome.tif")) is None
