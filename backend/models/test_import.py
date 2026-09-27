import sys
print("Python executable:", sys.executable)
print("Python version:", sys.version)

try:
    import numpy
    print("NumPy imported successfully, version:", numpy.__version__)
except Exception as e:
    print("Failed to import numpy:", e)

try:
    import sklearn
    print("Scikit-learn imported successfully, version:", sklearn.__version__)
except Exception as e:
    print("Failed to import sklearn:", e)

try:
    import joblib
    print("Joblib imported successfully, version:", joblib.__version__)
except Exception as e:
    print("Failed to import joblib:", e)
