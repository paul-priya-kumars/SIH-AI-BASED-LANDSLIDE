#!/usr/bin/env python3
"""
Detailed inspection of HDF5 file structure to find any hidden metadata.
"""

import os
import h5py
import numpy as np

def inspect_h5_detailed(file_path):
    """Inspect an HDF5 file in detail."""
    print(f"Detailed inspection of: {file_path}")
    print("=" * 60)

    def print_attrs(name, obj):
        print(f"  Examining: {name}")
        if hasattr(obj, 'attrs') and len(obj.attrs) > 0:
            for attr_name in obj.attrs:
                attr_value = obj.attrs[attr_name]
                print(f"    Attribute '{attr_name}': {attr_value} (type: {type(attr_value)})")

        if isinstance(obj, h5py.Dataset):
            print(f"    Dataset: shape={obj.shape}, dtype={obj.dtype}")
            # Show a sample of the data
            if obj.size < 100:  # Only show small datasets completely
                print(f"    Data: {obj[()]}")
            else:
                # Show corner and center samples
                print(f"    Data sample (corner): {obj[tuple([0]*len(obj.shape))]}")
                center_indices = tuple([s//2 for s in obj.shape])
                print(f"    Data sample (center): {obj[center_indices]}")
        elif isinstance(obj, h5py.Group):
            print(f"    Group")

    try:
        with h5py.File(file_path, 'r') as f:
            print("Visiting all items in file:")
            f.visititems(print_attrs)

    except Exception as e:
        print(f"Error inspecting {file_path}: {e}")
        import traceback
        traceback.print_exc()

def main():
    # Inspect a couple of different files
    dataset_dir = r"C:\Users/jayav/OneDrive/Desktop/land 2/datasets/landslide4sense/train/images"

    files = []
    for fname in sorted(os.listdir(dataset_dir)):  # Sort for consistent selection
        if fname.endswith('.h5'):
            files.append(os.path.join(dataset_dir, fname))
            if len(files) >= 2:
                break

    for file_path in files:
        inspect_h5_detailed(file_path)
        print("\n" + "=" * 80 + "\n")

if __name__ == "__main__":
    main()