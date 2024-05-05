#!/bin/bash
#SBATCH -t 7-00:00:00
#SBATCH -p gpu4_long,gpu8_long
#SBATCH -N 1
#SBATCH --mem=200G
#SBATCH --tasks-per-node=1
#SBATCH --cpus-per-task=10
#SBATCH --gres=gpu:1
#SBATCH --job-name=pretrain_MAE
#SBATCH --output=/gpfs/scratch/ss14424/Brain/logs/pretrain_%j.log

#unset PYTHONPATH
#module load anaconda3/gpu/5.2.0
#source activate /gpfs/home/ss14424/.conda/envs/canvas-env
#module unload anaconda3/gpu/5.2.0

torchrun \
    --standalone \
    --nnodes=1 \
    --nproc_per_node=10 \
    /gpfs/scratch/ss14424/singlecell/src/model/main_pretrain.py \
        --epoch 1 \
        --batch_size 32 \
        --tile_size 10 \
        --output_dir "/gpfs/scratch/ss14424/Brain/cells/model_output" \
        --log_dir "/gpfs/scratch/ss14424/Brain/logs" \
        --data_path "/gpfs/scratch/ss14424/Brain/cells/img_output"