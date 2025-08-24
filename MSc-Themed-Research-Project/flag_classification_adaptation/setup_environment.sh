#!/bin/bash
echo "Setting up conda environment for flag classification..."

# Create conda environment
conda create -n flag_classification python=3.10 -y
echo "Activating environment..."
conda activate flag_classification

# Install PyTorch with MPS support for M4 Max
pip3 install torch torchvision torchaudio

# Install project dependencies
pip install dassl-pytorch
pip install open-clip-torch
pip install timm
pip install yacs
pip install pandas numpy pillow
pip install scikit-learn matplotlib seaborn
pip install tensorboard

echo "✅ Environment setup complete!"
echo "To activate: conda activate flag_classification"
