import numpy as np
import zarr
from napari_zarr_io import napari_get_reader
from pathlib import Path 

# tmp_path is a pytest fixture
def test_reader(tmp_path):
    """Test reader"""
    pixels = np.random.rand(512, 512, 3)
    
    # Simple RGB image (Y,X,C)
    test_rgb_path = str(tmp_path / 'rgb_astronaut.zarr')
    rgb = zarr.open(
        test_rgb_path, 
        shape=pixels.shape, 
        chunks=(None, None, 3), 
        dtype=pixels.dtype
    )
    rgb[:] = pixels
    
    # try to read it back in
    reader = napari_get_reader(test_rgb_path)
    assert callable(reader)

    # make sure we're delivering the right format
    layer_data_list = reader(test_rgb_path)
    assert isinstance(layer_data_list, list) and len(layer_data_list) == 1
    layer_data_tuple = layer_data_list[0]
    assert isinstance(layer_data_tuple, tuple) and len(layer_data_tuple) > 0
    
    # make sure it's the same as it started
    np.testing.assert_allclose(pixels, np.asarray(layer_data_tuple[0]))
    
    # RGB image split into different channel arrays
    red = pixels[:,:,0]
    green = pixels[:,:,1]
    blue = pixels[:,:,2]

    test_channels_path = tmp_path / 'channels_astronaut.zarr'
    test_channels_path_grp = str(test_channels_path)
    grp = zarr.open_group(test_channels_path_grp)
    grp.create_dataset('red', data=red)
    grp.create_dataset('green', data=green)
    grp.create_dataset('blue', data=blue)
    
    # try to read it back in
    reader = napari_get_reader(test_channels_path_grp)
    assert callable(reader)

    # make sure we're delivering the right format
    layer_data_list = reader(test_channels_path_grp)
    assert isinstance(layer_data_list, list) and len(layer_data_list) == 3
    layer_data_tuple = layer_data_list[0]
    assert isinstance(layer_data_tuple, tuple) and len(layer_data_tuple) > 0

    # make sure it's the same as it started (layers sorted by name)
    np.testing.assert_array_equal(blue, np.asarray(layer_data_tuple[0]))
    np.testing.assert_array_equal(green, np.asarray(layer_data_list[1][0]))
    np.testing.assert_array_equal(red, np.asarray(layer_data_list[2][0]))

    # open just an array within group
    test_red_path = str(test_channels_path / 'red')
    reader = napari_get_reader(test_red_path)
    layer_data_list = reader(test_red_path)
    np.testing.assert_array_equal(red, np.asarray(layer_data_list[0][0]))


def test_get_reader_pass(tmp_path):
    
    # Remotely hosted
    reader = napari_get_reader("http://my_dataset.zarr")
    assert reader is None
    
    reader = napari_get_reader("https://my_dataset.zarr")
    assert reader is None
    
    reader = napari_get_reader("gc://my_dataset.zarr")
    assert reader is None
    
    reader = napari_get_reader("s3://my_dataset.zarr")
    assert reader is None

    # multiscale mock
    multiscale_mock = str(tmp_path / 'multiscale.zarr')
    grp = zarr.open_group(multiscale_mock)
    grp.attrs['multiscales'] = []
    reader = napari_get_reader(multiscale_mock)
    assert reader is None
