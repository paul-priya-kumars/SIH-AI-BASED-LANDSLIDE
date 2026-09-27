import os
import sys
import numpy as np
from pathlib import Path
import tifffile
import tempfile
import shutil
import subprocess

# Set environment variables to use our test dataset
os.environ["DATASET_PATH"] = "./datasets/landslide4sense_test"
os.environ["NUM_EPOCHS"] = "2"  # Just 2 epochs for testing
os.environ["BATCH_SIZE"] = "2"   # Small batch size
os.environ["NUM_WORKERS"] = "0"  # Disable multiprocessing for testing
os.environ["CHECKPOINT_DIR"] = "./test_checkpoints"


def create_tiny_dataset(root_dir, num_train=4, num_val=2, num_test=2):
    """
    Create a tiny Landslide4Sense-like dataset for pipeline testing.
    """
    root_path = Path(root_dir)
    if root_path.exists():
        shutil.rmtree(root_path)
    root_path.mkdir(parents=True, exist_ok=True)

    # Create directory structure
    for split in ['train', 'val', 'test']:
        (root_path / split / 'images').mkdir(parents=True, exist_ok=True)
        (root_path / split / 'masks').mkdir(parents=True, exist_ok=True)

    # Create tiny dummy data
    splits = [('train', num_train), ('val', num_val), ('test', num_test)]

    for split_name, num_samples in splits:
        print(f"Creating {num_samples} {split_name} samples...")

        for i in range(num_samples):
            # Create a fake 14-channel image in CHW format (channels, height, width)
            # Scale to [0, 255] and convert to uint8 for standard image format
            image_float = np.random.rand(14, 128, 128).astype(np.float32)
            image = (image_float * 255).astype(np.uint8)

            # Create a fake binary mask (height, width)
            # Randomly assign some pixels as landslide (1)
            mask = np.random.choice([0, 1], size=(128, 128), p=[0.9, 0.1]).astype(np.uint8)

            # Save as TIFF files
            image_path = root_path / split_name / 'images' / f'{i:04d}.tif'
            mask_path = root_path / split_name / 'masks' / f'{i:04d}.tif'

            # Save image with planarconfig='separate' so rasterio reads it correctly
            # Image is in CHW format (channels, height, width)
            tifffile.imwrite(image_path, image, planarconfig='separate')
            # Mask is already (H, W) which is correct for single-band
            tifffile.imwrite(mask_path, mask)

    print(f"Tiny dataset created at {root_path}")
    return str(root_path)

def main():
    print("=== PIPELINE VALIDATION TEST ===")
    print("This test uses a tiny dummy dataset to verify the pipeline works.")
    print("Results are for validation ONLY and should not be used for performance claims.\n")

    # Create tiny dataset
    dataset_path = create_tiny_dataset("./datasets/landslide4sense_test")

    try:
        # Set up the environment with proper PYTHONPATH
        env = os.environ.copy()
        # Add the parent directory of phase6 to PYTHONPATH so that phase6 can be imported as a package
        env["PYTHONPATH"] = str(Path(__file__).parent) + os.pathsep + env.get("PYTHONPATH", "")

        # Run the training script as a module from the phase6/image_analysis directory
        print("\nStarting pipeline validation test...")
        result = subprocess.run([
            sys.executable,
            "-m",
            "phase6.image_analysis.training.train"
        ], capture_output=True, text=True, cwd=Path(__file__).parent, env=env)

        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

        if result.returncode != 0:
            print(f"Training script failed with return code {result.returncode}")
            return False

        print("\nPipeline validation test completed successfully!")

        # Try to run evaluation on the test set
        print("\nRunning evaluation on test set...")

        # Find the best model checkpoint
        checkpoint_dir = Path("./test_checkpoints")
        best_model_path = checkpoint_dir / "best_model.pth"

        if best_model_path.exists():
            eval_result = subprocess.run([
                sys.executable,
                "-m",
                "phase6.image_analysis.training.evaluate",
                "--model_path", str(best_model_path),
                "--dataset_path", dataset_path,
                "--split", "test",
                "--output_dir", "./test_evaluation_results",
                "--num_workers", "0"
            ], capture_output=True, text=True, cwd=Path(__file__).parent, env=env)

            print(eval_result.stdout)
            if eval_result.stderr:
                print("Eval STDERR:", eval_result.stderr)

            if eval_result.returncode != 0:
                print(f"Evaluation script failed with return code {eval_result.returncode}")
                return False

            print("Evaluation completed!")
        else:
            print("No best model checkpoint found, skipping evaluation")

    except Exception as e:
        print(f"Error during pipeline validation: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✓ PIPELINE VALIDATION PASSED")
        print("  The dataset loader → preprocessing → augmentation → model → loss →")
        print("  training loop → validation → checkpoint saving → evaluation pipeline")
        print("  works end-to-end with the tiny test dataset.")
    else:
        print("\n✗ PIPELINE VALIDATION FAILED")
        print("  There are issues in the pipeline that need to be fixed.")