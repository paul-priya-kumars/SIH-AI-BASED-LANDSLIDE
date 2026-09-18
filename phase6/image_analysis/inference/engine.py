"""
Inference engine for Landslide4Sense satellite imagery.

Defines the interface for running inference on satellite imagery.
In Phase 3, performs actual inference when model is available.
"""

from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import time
import torch
import numpy as np

from phase6.image_analysis.models.loader import (
    Landslide4SenseModelLoader,
    ImageModelNotAvailableError
)
from phase6.image_analysis.preprocessing.landslide4sense import (
    Landslide4SensePreprocessor
)


class Landslide4SenseInferenceError(Exception):
    """Raised when an error occurs during inference processing."""


class Landslide4SenseInferenceEngine:
    """
    Inference engine for Landslide4Sense satellite imagery.

    Coordinates:
    - Preprocessing of input data
    - Model inference
    - Postprocessing of results
    - Conversion to risk levels

    In Phase 3:
    - Performs actual inference when model is available and AI is enabled
    - Returns proper error responses when conditions are not met
    """

    def __init__(
        self,
        preprocessor: Optional[Landslide4SensePreprocessor] = None,
        model_loader: Optional[Landslide4SenseModelLoader] = None
    ):
        """
        Initialize the inference engine.

        Args:
            preprocessor: Preprocessor instance. If None, creates default.
            model_loader: Model loader instance. If None, creates default.
        """
        self.preprocessor = preprocessor if preprocessor is not None else Landslide4SensePreprocessor()
        self.model_loader = model_loader if model_loader is not None else Landslide4SenseModelLoader()

    def is_ready(self) -> bool:
        """
        Check if the inference engine is ready to run inference.

        Returns:
            True if preprocessor is configured and model is available, False otherwise
        """
        # Preprocessor is always considered configured in our implementation
        preprocessor_ready = True

        # Model availability depends on configuration and file existence
        model_available = self.model_loader.is_model_available()

        return preprocessor_ready and model_available

    def run_inference(self, sample_path: Path) -> Dict[str, Any]:
        """
        Run inference on a Landslide4Sense sample.

        Args:
            sample_path: Path to the input sample file

        Returns:
            Dictionary containing inference results or error information
        """
        start_time = time.time()

        try:
            # Check if input path exists (basic validation)
            if not sample_path.exists():
                return self._create_error_response(
                    "INPUT_FILE_NOT_FOUND",
                    f"Input file not found: {sample_path}",
                    start_time
                )

            # Check if inference engine is ready
            if not self.is_ready():
                # Determine why it's not ready for better error messaging
                from phase6.image_analysis.config import get_image_ai_config
                config = get_image_ai_config()

                if not config.is_image_ai_enabled():
                    return self._create_error_response(
                        "IMAGE_AI_DISABLED",
                        "Image AI is disabled via configuration (JARVIS_IMAGE_AI_ENABLED=false)",
                        start_time
                    )
                elif not self.model_loader.is_model_available():
                    return self._create_error_response(
                        "MODEL_NOT_AVAILABLE",
                        f"IMAGE MODEL NOT AVAILABLE: {self.model_loader.model_path}",
                        start_time
                    )
                else:
                    return self._create_error_response(
                        "INFERENCE_NOT_READY",
                        "Inference engine not ready for unknown reasons",
                        start_time
                    )

            # Load the actual sample data
            try:
                # Load sample using preprocessor
                sample_data = self.preprocessor.load_sample(sample_path)
            except Exception as e:
                return self._create_error_response(
                    "SAMPLE_LOADING_FAILED",
                    f"Failed to load sample: {str(e)}",
                    start_time
                )

            # Preprocess the sample
            try:
                processed_sample = self.preprocessor.preprocess_sample(sample_data)
            except Exception as e:
                return self._create_error_response(
                    "SAMPLE_PREPROCESSING_FAILED",
                    f"Failed to preprocess sample: {str(e)}",
                    start_time
                )

            # Get the model and run inference
            try:
                model = self.model_loader.load_model()
                model.eval()  # Ensure model is in evaluation mode
            except Exception as e:
                return self._create_error_response(
                    "MODEL_LOADING_FAILED",
                    f"Failed to load model: {str(e)}",
                    start_time
                )

            # Convert processed sample to tensor and add batch dimension
            try:
                # Ensure we have the right shape (C, H, W) from preprocessor
                if processed_sample.ndim != 3:
                    return self._create_error_response(
                        "INVALID_SAMPLE_SHAPE",
                        f"Processed sample must be 3-dimensional (C, H, W), got shape {processed_sample.shape}",
                        start_time
                    )

                # Convert to tensor and add batch dimension: (C, H, W) -> (1, C, H, W)
                sample_tensor = torch.from_numpy(processed_sample).unsqueeze(0).to(self.model_loader.device)
            except Exception as e:
                return self._create_error_response(
                    "TENSOR_CONVERSION_FAILED",
                    f"Failed to convert sample to tensor: {str(e)}",
                    start_time
                )

            # Run inference
            try:
                with torch.inference_mode():
                    logits = model(sample_tensor)
                    probs = torch.sigmoid(logits)  # Convert logits to probabilities
            except Exception as e:
                return self._create_error_response(
                    "INFERENCE_EXECUTION_FAILED",
                    f"Inference execution failed: {str(e)}",
                    start_time
                )

            # Process results to extract pixel-level and image-level probabilities
            try:
                # Handle different output shapes
                if probs.shape[1] == 2:
                    # Binary classification with 2 channels: take probability of positive class (index 1)
                    probs = probs[:, 1:2, :, :]  # shape: (1, 1, 128, 128)
                # If already shape (1, 1, H, W), use as is
                elif probs.shape[1] != 1:
                    return self._create_error_response(
                        "UNEXPECTED_OUTPUT_SHAPE",
                        f"Unexpected model output shape: {probs.shape}. Expected (1, 1, H, W) or (1, 2, H, W)",
                        start_time
                    )

                # Convert to numpy and extract the probability map
                probs_np = probs.squeeze().cpu().numpy()  # shape: (H, W)

                # Validate output shape
                expected_shape = (128, 128)
                if probs_np.shape != expected_shape:
                    return self._create_error_response(
                        "UNEXPECTED_OUTPUT_SHAPE",
                        f"Model output probability map has unexpected shape: {probs_np.shape}. Expected {expected_shape}",
                        start_time
                    )

                # Calculate image-level landslide probability
                # Using maximum probability as an indicator of landslide presence in the patch
                image_level_probability = float(np.max(probs_np))

                # Alternative approaches (commented for clarity):
                # image_level_probability = float(np.mean(probs_np))  # average probability
                # image_level_probability = float(np.sum(probs_np > 0.5) / probs_np.size)  # fraction of pixels above threshold

                # Clamp probability to valid range [0, 1]
                image_level_probability = max(0.0, min(1.0, image_level_probability))

                # Get the preprocessor for potential use in response
                preprocessor = self.model_loader.get_preprocessor()

                processing_time_ms = int((time.time() - start_time) * 1000)

                return {
                    "success": True,
                    "pixel_probabilities": probs_np.tolist(),  # Return as list for JSON serialization
                    "image_level_probability": image_level_probability,
                    "processing_time_ms": processing_time_ms,
                    "model_available": True,
                    "model_version": self.model_loader.model_version,
                    "timestamp": time.time(),
                    "note": "Real inference performed using Landslide4Sense model"
                }

            except Exception as e:
                return self._create_error_response(
                    "RESULT_PROCESSING_FAILED",
                    f"Failed to process inference results: {str(e)}",
                    start_time
                )

        except Exception as e:
            # Handle unexpected errors during inference setup
            return self._create_error_response(
                "INFERENCE_FAILURE",
                f"Inference failed: {str(e)}",
                start_time
            )

    def _create_error_response(self, error_code: str, error_message: str, start_time: float) -> Dict[str, Any]:
        """
        Create a standardized error response dictionary.

        Args:
            error_code: Machine-readable error code
            error_message: Human-readable error message
            start_time: Start time from time.time() for calculating duration

        Returns:
            Dictionary with error response format
        """
        processing_time_ms = int((time.time() - start_time) * 1000)

        from phase6.image_analysis.config import get_image_ai_config
        config = get_image_ai_config()

        return {
            "success": False,
            "error": error_message,
            "error_code": error_code,
            "processing_time_ms": processing_time_ms,
            "model_available": self.model_loader.is_model_available(),
            "model_version": self.model_loader.model_version,
            "timestamp": time.time()  # Simple timestamp for now
        }

    def get_engine_status(self) -> Dict[str, Any]:
        """
        Get the current status of the inference engine.

        Returns:
            Dictionary with engine status information
        """
        from phase6.image_analysis.config import get_image_ai_config
        config = get_image_ai_config()

        return {
            "engine_ready": self.is_ready(),
            "preprocessor_configured": True,  # Our preprocessor is always configured
            "preprocessor_fitted": self.preprocessor.is_fitted(),
            "model_loader_info": self.model_loader.get_model_info(),
            "can_run_inference": self.is_ready(),
            "image_ai_enabled": config.is_image_ai_enabled()
        }

    def __repr__(self) -> str:
        """String representation of the inference engine."""
        return (
            f"Landslide4SenseInferenceEngine("
            f"preprocessor={self.preprocessor}, "
            f"model_loader={self.model_loader})"
        )