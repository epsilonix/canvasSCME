# Converting QPTIFF to Zarr with channel metadata
import os
import xml.etree.ElementTree as ET
import tifffile
import zarr


def qptiff_to_zarr(input_file, output_root, chunk_size=(None, 256, 256)):
    # Check if output file already exists
    output_path = os.path.join(output_root, os.path.basename(input_file).replace('.tif', ''))
    output_zarr = output_path + '/data.zarr'
    print(f'Create the directory')

    os.makedirs(output_path, exist_ok=True)
    
    
    # Check if Zarr dataset already exists at the path
    if os.path.exists(output_zarr) and zarr.is_zarr(output_zarr):
        print(f"Zarr dataset already exists at {output_zarr}. Consider handling this scenario appropriately.")
        # Options: return existing dataset, delete and recreate, etc.
        return zarr.open(output_zarr, mode='a')  # Open in append mode as a placeholder action
    
    # Read the QPTIFF file
    print(f'Read the tif file')
    with tifffile.TiffFile(input_file) as tif:
        for page in tif.pages:
            print(page.shape)
        img_data = tif.asarray()

    
    z_arr = zarr.array(img_data, chunks=chunk_size, store=output_zarr)
    return z_arr
