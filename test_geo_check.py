import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))
sys.path.insert(0, os.path.dirname(__file__))

from app.services.risk_service import _check_geographic_metadata_available
print("Geographic metadata available:", _check_geographic_metadata_available())