import numpy as np
import pandas as pd
import os
import torch.utils.data as data
from torchvision import transforms
from skimage.io import imsave, imread
from skimage.transform import resize

class SlideDataset(data.Dataset):
    ''' Dataset for slides '''

    def __init__(self, root_path=None, tile_size=None, transform=None):
        ''' 
        Initialize the dataset 
        root_path: root path of the dataset (for saving processed file purposes)
        '''
        self.root_path = root_path
        self.tile_size = tile_size
        self.transform = transform

        if tile_size is not None:
            # Load tiles positions from disk
            self.tile_pos = self.load_tiles(tile_size)

    def __getitem__(self, index):
        image = self.read_region(self.tile_pos[index][0], self.tile_pos[index][1], self.tile_size, self.tile_size)
        if self.transform is not None:
            transformed_image = self.transform(image)
        else:
            transformed_image = transforms.ToTensor()(image)
        label = None
        x = self.tile_pos[index][0]
        y = self.tile_pos[index][1]
        img_id = index
        return transformed_image, label, x, y, img_id

    def __len__(self):
        return len(self.tile_pos)

    def read_slide(self, root_path):
        ''' Read slide from disk'''
        raise NotImplementedError

    def read_region(self, pos_x, pos_y, width, height):
        ''' x and y are the coordinates of the top left corner '''
        raise NotImplementedError

    def get_slide_dimensions(self):
        ''' Get slide dimensions '''
        raise NotImplementedError

    def save_thumbnail(self):
        ''' Save a thumbnail of the slide '''
        raise NotImplementedError

    def load_tiles(self, tile_size):
        ''' Load tile positions from disk and save cell types to celltype.npy '''
        tile_path = f'{self.root_path}/tiles/positions_{tile_size}.csv'
        df = pd.read_csv(tile_path)

        # Extract the tile positions and cell types
        tile_pos = df[["h", "w"]].to_numpy()
#        cell_types = df["celltype"].values
#        
#        
#        print(f'now processing {tile_path} which has {len(cell_types)} cells')
#
#        # Define the path where the cell types will be saved
#        save_path = '/gpfs/scratch/ss14424/Brain/cells_csd/analysis_output/celltype.npy'
#        directory = os.path.dirname(save_path)
#
#        # Ensure the directory exists
#        os.makedirs(directory, exist_ok=True)
#
#        # Check if the file exists
#        if os.path.exists(save_path):
#            # Load existing data with allow_pickle=True
#            existing_data = np.load(save_path, allow_pickle=True)
#            # Ensure existing_data is of the same type as cell_types
#            if isinstance(existing_data, np.ndarray) and existing_data.dtype == cell_types.dtype:
#                # Concatenate the new cell types with the existing data
#                cell_types = np.concatenate((existing_data, cell_types))
#            else:
#                raise ValueError("Data type mismatch or incompatible data structure in existing file")
#
#        # Save the concatenated cell types to a NumPy file
#        np.save(save_path, cell_types)
#        print(f"Cell types saved to {save_path}")

        return tile_pos

    # Generate tiles from mask
    def load_tiling_mask(self, mask_path, tile_size):
        ''' Load tissue mask to generate tiles '''
        # Get slide dimensions
        slide_width, slide_height = self.get_slide_dimensions()
        # Specify grid size
        grid_width, grid_height = slide_width // tile_size, slide_height // tile_size
        # Create mask
        if mask_path is not None: # Load mask from existing file
            mask_temp = np.array(imread(mask_path)).swapaxes(0, 1)
            assert abs(mask_temp.shape[0] / mask_temp.shape[1] - slide_width / slide_height) < 0.01, 'Mask shape does not match slide shape'
            # Convert mask to patch-pixel level grid
            mask = resize(mask_temp, (grid_width, grid_height), anti_aliasing=False)
        else:
            mask = np.ones((grid_width, grid_height)) # Tile all regions
        return mask

    def generate_tiles(self, tile_size, mask_path=None, mask_id='default', threshold=0.99):
        ''' 
        Generate tiles from a slide
        threshold: minimum percentage of tissue mask in a tile
        '''
        # Load mask
        mask = self.load_tiling_mask(mask_path, tile_size)
        # Generate tile coordinates according to masked grid
        ws, hs = np.where(mask >= threshold)
        positions = (np.array(list(zip(ws, hs))) * tile_size)
        # Save tile top left positions
        tile_path = f'{self.root_path}/tiles/{mask_id}'
        save_path = f'{tile_path}/{tile_size}'
        os.makedirs(save_path, exist_ok=True)
        np.save(f'{save_path}/tile_positions_top_left.npy', positions)
        # Save mask image
        mask_img = np.zeros_like(mask)
        mask_img[ws, hs] = 1
        imsave(f'{save_path}/mask.png', (mask_img.swapaxes(0, 1) * 255).astype(np.uint8))
