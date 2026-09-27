"""
Landslide4Sense preprocessing package.
"""

from .landslide4sense import Landslide4SensePreprocessor


def get_default_preprocessor() -> Landslide4SensePreprocessor:
    """Get the default preprocessor instance."""
    return Landslide4SensePreprocessor()