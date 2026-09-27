import sys
import os
# Set environment variables for the model and AI enablement
os.environ["JARVIS_IMAGE_AI_ENABLED"] = "true"
os.environ["JARVIS_IMAGE_MODEL_PATH"] = "checkpoints/best_model.pth"

import time
import numpy as np
from pathlib import Path

sys.path.insert(0, '.')

from phase6.image_analysis.inference.engine import Landslide4SenseInferenceEngine
from phase6.image_analysis.models.loader import Landslide4SenseModelLoader
from phase6.image_analysis.preprocessing.landslide4sense import Landslide4SensePreprocessor

def main():
    print("=== BASELINE FOR PHASE 4 ===")
    
    # Initialize components
    print("Initializing inference engine...")
    engine = Landslide4SenseInferenceEngine()
    
    # Check if model is available
    model_available = engine.model_loader.is_model_available()
    print(f"Model available: {model_available}")
    
    if not model_available:
        print("ERROR: Model is not available. Cannot run baseline.")
        return
    
    # Time model loading
    print("\nTiming model loading...")
    start_time = time.time()
    model = engine.model_loader.load_model()
    model_load_time = time.time() - start_time
    print(f"Model load time: {model_load_time:.3f} seconds")
    
    # Get model info
    model_info = engine.model_loader.get_model_info()
    print(f"Model version: {model_info.get('model_version', 'unknown')}")
    print(f"Model path: {model_info.get('model_path', 'unknown')}")
    
    # Get preprocessor info
    print(f"Preprocessor fitted: {engine.preprocessor.is_fitted()}")
    
    # Define test samples
    test_samples = [
        Path("datasets/landslide4sense/test/images/image_100.h5"),
        Path("datasets/landslide4sense/test/images/image_1005.h5"),
        Path("datasets/landslide4sense/test/images/image_101.h5")
    ]
    
    # Check that samples exist
    for sample in test_samples:
        if not sample.exists():
            print(f"ERROR: Sample not found: {sample}")
            return
    
    print(f"\nRunning inference on {len(test_samples)} samples...")
    
    # Run inference on each sample and collect results
    inference_times = []
    input_shapes = []
    output_shapes = []
    probabilities = []
    
    for i, sample_path in enumerate(test_samples):
        print(f"\nSample {i+1}: {sample_path.name}")
        start_time = time.time()
        result = engine.run_inference(sample_path)
        inference_time = time.time() - start_time
        inference_times.append(inference_time)
        
        if result["success"]:
            print(f"  Success: True")
            print(f"  Inference time (from result): {result.get('processing_time_ms', 0)} ms")
            print(f"  Inference time (wall clock): {inference_time:.3f} seconds")
            
            # Get pixel probabilities shape
            pixel_probs = result.get("pixel_probabilities")
            if pixel_probs is not None:
                # The pixel probabilities are returned as a flattened list
                # We know the shape should be 128x128
                prob_array = np.array(pixel_probs)
                print(f"  Pixel probabilities shape: {prob_array.shape}")
                input_shapes.append((128, 128, 14))  # We know the input shape
                output_shapes.append(prob_array.shape)  # This is (128*128,) flattened
                # Also get the image level probability
                img_prob = result.get("image_level_probability")
                print(f"  Image-level probability: {img_prob:.6f}")
                probabilities.append(img_prob)
            else:
                print("  WARNING: No pixel probabilities in result")
        else:
            print(f"  Success: False")
            print(f"  Error: {result.get('error', 'unknown')}")
    
    # Calculate averages
    if inference_times:
        avg_inference_time = np.mean(inference_times)
        print(f"\n=== SUMMARY ===")
        print(f"Average inference time (wall clock): {avg_inference_time:.3f} seconds")
        print(f"Model load time: {model_load_time:.3f} seconds")
        print(f"Number of samples: {len(test_samples)}")
        print(f"All samples processed successfully: {all(r['success'] for r in [engine.run_inference(p) for p in test_samples])}")
        
        # Save baseline results to a file for later comparison
        baseline_data = {
            "model_load_time": model_load_time,
            "average_inference_time": avg_inference_time,
            "inference_times": inference_times,
            "input_shapes": input_shapes,
            "output_shapes": output_shapes,
            "probabilities": probabilities,
            "model_info": model_info
        }
        
        import json
        # Convert numpy arrays to lists for JSON serialization
        def convert_for_json(obj):
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, dict):
                return {k: convert_for_json(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_for_json(i) for i in obj]
            else:
                return obj
        
        baseline_data_json = convert_for_json(baseline_data)
        with open("baseline_results.json", "w") as f:
            json.dump(baseline_data_json, f, indent=2)
        print(f"Baseline results saved to baseline_results.json")
    else:
        print("ERROR: No successful inferences to summarize.")

if __name__ == "__main__":
    main()
