import os
import zarr
import numpy as np
from skimage.measure import block_reduce
from skimage.io import imsave
from scipy.io import loadmat
import matplotlib.pyplot as plt
import random
import json

colors = [
    (0, 0, 139),  # cd117, mast cell, myeloid, darkblue
    (173, 216, 230),  # cd11c, myeloid, lightblue
    (135, 206, 250),  # cd14, myeloid, lightblue
    (212, 226, 228),  # cd163, myeloid, lightblue
    (70, 130, 180),  # cd16, monocyte, mid blue
    (149, 229, 68),  # cd20, b cell, green
    (25, 25, 112),  # cd31, stromal, dark blue
    (228, 82, 50),  # cd3, t cell, orange
    (255, 165, 0),  # cd4, t cell, orange
    (176, 226, 219),  # cd68, myeloid, lightblue
    (255, 140, 0),  # cd8a, t cell, orange
    (255, 127, 80),  # cd94, t cell, orange
    (228, 71, 184),  # dna1, dna, grey
    (255, 99, 71),  # foxp3, t cell, orange
    (255, 182, 193),  # GFAP
    (176, 226, 219),  # hla-dr, antigen, lightgreen
    (73, 52, 229),  # mpo, neutrophil, purple
    (0, 255, 255),  # Olig2
    (255, 255, 0),  # P2PY12
    (238, 130, 238),  # Sox2
    (50, 205, 50),  # Sox9
    (255, 20, 147),  # MeLanA, pink
    (186, 85, 211),  # PMEL, medium orchid
    (0, 128, 0),    # PanCK, green 
    (0, 0, 0),
    (0, 0, 0),
    (0, 0, 0),
    (0, 0, 0),
    (0, 0, 0),
    (0, 0, 0),
    (0, 0, 0),
    (0, 0, 0),
    (0, 0, 0),
    (0, 0, 0),
    (0, 0, 0),
    (0, 0, 0),
    (0, 0, 0),
    (0, 0, 0),
    (0, 0, 0),
    (0, 0, 0),
    (0, 0, 0)
]

very_common_cell_types = {'Cancer', 'Astrocytes', 'Cl BMDM', 'Alt BMDM', 'Endothelial cell', 'Cl MG', 'Alt MG'}

def calculate_polygon_area(coords):
    """Calculate the area of a polygon using the shoelace formula.

    Args:
    - coords (list of tuples): List of (x, y) tuples for each vertex of the polygon.

    Returns:
    - float: The area of the polygon.
    """
    x = np.array([coord[0] for coord in coords])
    y = np.array([coord[1] for coord in coords])

    return 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))

def gen_tiles(image, slide: str, mat_path, tile_size: int = 20, 
              output_path: str = None, image_filename: str = None,
              mode: str = 'full') -> np.ndarray:
    ''' Generate tiles for a given slide '''
    print(f'Slide type is {type(slide)}')
    if output_path is None: output_path = f'{os.path.dirname(slide)}'
    output_path += '/tiles/'
    os.makedirs(output_path, exist_ok=True)
    
    # Read slide
    print('Reading slide...')
    print(f'IMG has a dimension of {slide.shape}')
    if isinstance(slide, str):
        slide = zarr.load(slide)
    print(f'ZARR IMG has a dimension of {slide.shape}')
    
    # Extract 'Boundaries' and 'cellTypes' data
    boundaries_info = mat_path['Boundaries']
    cell_types = mat_path['cellTypes']

    # Correct dimensions of the image
    correct_dimensions = image.shape[1:3][::-1]  # Assuming 'image' is defined elsewhere

    # Initialize a list to hold the coordinates for all boundaries
    all_boundaries_coords = []

    for i in range(boundaries_info.shape[1]):
        # Extract linear indices for the current boundary
        linear_indices = boundaries_info[0, i].flatten()  # Ensure it's a 1D array

        # Convert linear indices to x and y coordinates
        x_coords, y_coords = np.unravel_index(linear_indices, correct_dimensions)

        # Store the coordinates as tuples in the list
        boundary_coords = list(zip(x_coords, y_coords))

        # Calculate the area of the boundary
        area = calculate_polygon_area(boundary_coords)

        # Get the corresponding cell type, handle empty or undefined types
        cell_type = cell_types[i][0][0] if cell_types[i][0].size > 0 else 'Unknown'

        if area > 20 and area < 200:
            all_boundaries_coords.append((boundary_coords, cell_type))

    # Assuming 'image' and 'colors' are defined elsewhere
    num_channels, height, width = image.shape
    brightness_factor = 3.0

    # Initialize a composite image with 3 channels for RGB
    composite_image = np.zeros((height, width, 3), dtype=np.float32)
    global_max = np.max(image)
    for i in range(num_channels):
        color = colors[i]
        channel_normalized = image[i, :, :] / global_max
        for j in range(3):  # RGB channels
            composite_image[:, :, j] += channel_normalized * color[j]

    # Normalize the composite image to be in the range [0, 1]
    composite_image = np.clip(composite_image / np.max(composite_image, axis=(0, 1)) * brightness_factor, 0, 1)

    # Plot the composite image
    plt.figure(figsize=(15, 15))  # Adjust the figure size as needed
    plt.imshow(composite_image)

    # Initialize list to keep track of centroids and their types
    positions = []

    # Dictionary to keep track of sampled cell counts in training mode
    sampled_cell_counts = {cell_type: 0 for cell_type in very_common_cell_types}

    # Sample boundaries based on the mode
    sample_boundaries_coords = []
    if mode == 'subsample':
        print(f'now in subsampling mode... taking subsample of slides...')
        # Sample up to 100 cells for very common cell types
        cell_type_groups = {cell_type: [] for cell_type in very_common_cell_types}
        other_cell_types = []

        for boundary_info in all_boundaries_coords:
            boundary_coords, cell_type = boundary_info
            if cell_type in very_common_cell_types:
                cell_type_groups[cell_type].append(boundary_info)
            else:
                other_cell_types.append(boundary_info)

        for cell_type, boundaries in cell_type_groups.items():
            sample_count = min(len(boundaries), 100)
            sampled_boundaries = random.sample(boundaries, sample_count)
            sample_boundaries_coords.extend(sampled_boundaries)
            sampled_cell_counts[cell_type] += sample_count

        sample_boundaries_coords.extend(other_cell_types)
        print(f'generated {len(sample_boundaries_coords)} slides')

    else:
        print(f'now in full mode... printing all slides...')
        sample_boundaries_coords = all_boundaries_coords.copy()
        print(f'generated {len(sample_boundaries_coords)} slides')

    # Plot each boundary and calculate centroids
    for boundary_info in sample_boundaries_coords:
        # Extract the boundary coordinates and cell type
        boundary_coords, cell_type = boundary_info

        # Convert list of tuples to a numpy array for easy slicing
        boundary_array = np.array(boundary_coords)
        plt.plot(boundary_array[:, 0], boundary_array[:, 1], color='cyan', linewidth=0.5)  # Adjust color and linewidth as desired

        # Calculate centroid
        centroid_x = int(np.round(np.mean(boundary_array[:, 0])))
        centroid_y = int(np.round(np.mean(boundary_array[:, 1])))

        # Size of the square centered on each centroid
        half_side_length = tile_size / 2  # Half the side length of the square, for a total side length of 10 pixels

        # Exclude centroids within 10 pixels of the boundary
        if 10 <= centroid_x <= width - 10 and 10 <= centroid_y <= height - 10:
            top_left_x = centroid_x - half_side_length
            top_left_y = centroid_y - half_side_length
            positions.append((top_left_y, top_left_x, cell_type, [(int(y), int(x)) for x, y in boundary_coords]))

    with open(os.path.join(output_path, f'positions_{tile_size}.csv'), 'w') as f:
        f.write(' ,h,w,celltype,boundary\n')
        for i, (h, w, celltype, boundary) in enumerate(positions):
            boundary_str = json.dumps(boundary)
            f.write(f'{i},{h},{w},{celltype},"{boundary_str}"\n')
    print(f'Generated {len(positions)} tiles for slide with shape {slide.shape}')

def save_img(output_path: str, task: str, tile_size: int, img: np.ndarray):
    ''' Save image to output path '''
    img = (np.clip(img, 0, 1) * 255).astype(np.uint8)
    imsave(os.path.join(output_path, f'{task}_{tile_size}.png'), img)

def gen_thumbnail(slide: zarr, scaling_factor: int) -> np.ndarray:
    ''' Generate thumbnail for a given slide '''
    # Make sure first channel is smaller than the second and third
    assert slide.shape[0] < slide.shape[1] and slide.shape[0] < slide.shape[2]
    cache = block_reduce(slide, 
                         block_size=(slide.shape[0], 
                                     scaling_factor, scaling_factor), 
                         func=np.mean)
    # Remove bright pixels top 5 percentile
    cache = np.clip(cache, 0, np.percentile(cache, 95))
    cache /= cache.max()
    thumbnail = np.clip(cache, 0, 1).squeeze()
    return thumbnail
