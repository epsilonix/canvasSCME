#!/bin/bash
#SBATCH -t 0-07:00:00
#SBATCH -p gpu4_long,gpu8_long
#SBATCH -N 1
#SBATCH --mem=100G
#SBATCH --tasks-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --gres=gpu:1
#SBATCH --job-name=preprocessing_MAE
#SBATCH --output=/gpfs/scratch/ss14424/logs/preprocess_%j.log

source activate /gpfs/home/ss14424/.conda/envs/canvas-env

python \
/gpfs/scratch/ss14424/singlecell/src/preprocessing/preprocess.py \
/gpfs/scratch/ss14424/Brain/data/tif_24_channels \
/gpfs/scratch/ss14424/Brain/data/celltype \
/gpfs/scratch/ss14424/Brain/channels_20/cells/img_output_20 \
20