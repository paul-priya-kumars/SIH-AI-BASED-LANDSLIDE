#!/usr/bin/env python3
"""
Inspect the checkpoint file to understand its format and test loading.
"""

import torch
import numpy as np
from pathlib import Path

def inspect_checkpoint(checkpoint_path):
    """Inspect a checkpoint file."""
    print(f"Inspecting checkpoint: {checkpoint_path}")

    if not Path(checkpoint_path).exists():
        print(f"ERROR: Checkpoint file not found at {checkpoint_path}")
        return False

    try:
        # Try to load the checkpoint with different approaches
        print("\n1. Trying to load with weights_only=True (PyTorch 2.6+ secure default):")
        try:
            checkpoint = torch.load(checkpoint_path, map_location='cpu', weights_only=True)
            print("   SUCCESS: Loaded with weights_only=True")
            print(f"   Checkpoint keys: {list(checkpoint.keys())}")
            if 'model_state_dict' in checkpoint:
                print(f"   Model state dict keys: {list(checkpoint['model_state_dict'].keys())[:5]}...")
            return True
        except Exception as e:
            print(f"   FAILED: {e}")

        print("\n2. Trying to load with weights_only=False:")
        try:
            checkpoint = torch.load(checkpoint_path, map_location='cpu', weights_only=False)
            print("   SUCCESS: Loaded with weights_only=False")
            print(f"   Checkpoint keys: {list(checkpoint.keys())}")
            if 'model_state_dict' in checkpoint:
                print(f"   Model state dict keys: {list(checkpoint['model_state_dict'].keys())[:5]}...")
            return True
        except Exception as e:
            print(f"   FAILED: {e}")

        print("\n3. Trying to add safe globals and load with weights_only=True:")
        try:
            # Add numpy scalar to safe globals
            torch.serialization.add_safe_globals([np._core.multiarray.scalar])
            checkpoint = torch.load(checkpoint_path, map_location='cpu', weights_only=True)
            print("   SUCCESS: Loaded with safe globals and weights_only=True")
            print(f"   Checkpoint keys: {list(checkpoint.keys())}")
            if 'model_state_dict' in checkpoint:
                print(f"   Model state dict keys: {list(checkpoint['model_state_dict'].keys())[:5]}...")
            return True
        except Exception as e:
            print(f"   FAILED: {e}")

        print("\n4. Trying to load with pickle protocol=None (let PyTorch choose):")
        try:
            checkpoint = torch.load(checkpoint_path, map_location='cpu', pickle_module=None)
            print("   SUCCESS: Loaded with pickle_module=None")
            print(f"   Checkpoint keys: {list(checkpoint.keys())}")
            if 'model_state_dict' in checkpoint:
                print(f"   Model state dict keys: {list(checkpoint['model_state_dict'].keys())[:5]}...")
            return True
        except Exception as e:
            print(f"   FAILED: {e}")

        return False

    except Exception as e:
        print(f"Unexpected error during inspection: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    checkpoint_path = "./checkpoints/best_model.pth"
    success = inspect_checkpoint(checkpoint_path)

    if success:
        print("\n" + "="*50)
        print("CHECKPOINT INSPECTION: SUCCESS")
        print("="*50)
    else:
        print("\n" + "="*50)
        print("CHECKPOINT INSPECTION: FAILED")
        print("="*50)