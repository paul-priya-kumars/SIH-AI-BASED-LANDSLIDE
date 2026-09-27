#!/usr/bin/env python3
"""
Inspect HDF5 metadata to understand what geographic information is available.
"""

import os
import h5py
import numpy as np

def inspect_h5_file(file_path):
    """Inspect an HDF5 file for metadata."""
    print(f"Inspecting: {file_path}")
    print("=" * 50)

    try:
        with h5py.File(file_path, 'r') as f:
            print("Top-level keys/datasets:")
            for key in f.keys():
                item = f[key]
                if isinstance(item, h5py.Dataset):
                    print(f"  {key}: shape={item.shape}, dtype={item.dtype}")
                elif isinstance(item, h5py.Group):
                    print(f"  {key}: Group")

            # Check for attributes
            print("\nFile-level attributes:")
            for attr_name in f.attrs:
                attr_value = f.attrs[attr_name]
                print(f"  {attr_name}: {attr_value}")

            # Check specific datasets for attributes
            print("\nDataset attributes:")
            for key in f.keys():
                if isinstance(f[key], h5py.Dataset):
                    print(f"  {key}:")
                    for attr_name in f[key].attrs:
                        attr_value = f[key].attrs[attr_name]
                        print(f"    {attr_name}: {attr_value}")

    except Exception as e:
        print(f"Error inspecting {file_path}: {e}")

def main():
    # Inspect a few different image files to see if they have different metadata
    dataset_dir = r"C:\Users\jayav\OneDrive\Desktop\land 2\datasets\landslide4sense\train\images"

    # Get a few files
    files = []
    for fname in os.listdir(dataset_dir):
        if fname.endswith('.h5'):
            files.append(os.path.join(dataset_dir, fname))
            if len(files) >= 3:  # Just inspect a few files
                break

    for file_path in files:
        inspect_h5_file(file_path)
        print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()