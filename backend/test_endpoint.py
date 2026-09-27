"""
Test the model info endpoint directly.
"""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_model_info_endpoint():
    """Test the model info endpoint and print the response."""
    print("Calling /api/ml/model-info endpoint...")
    response = client.get("/api/ml/model-info")

    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")

    if response.status_code == 200:
        data = response.json()
        print("\nResponse JSON:")
        for key, value in data.items():
            print(f"  {key}: {value} ({type(value).__name__})")

        # Verify required fields are present
        required_fields = ["available", "model_path", "model_version", "checksum", "load_time_seconds"]
        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            print(f"\n❌ Missing fields: {missing_fields}")
            return False
        else:
            print(f"\n✓ All required fields present: {required_fields}")

            # Additional validation
            if isinstance(data["available"], bool):
                print(f"  ✓ 'available' is boolean: {data['available']}")
            else:
                print(f"❌ 'available' is not boolean: {data['available']}")

            if isinstance(data["model_path"], str) or data["model_path"] is None:
                print(f"✅ 'model_path' is string or None: {data['model_path']}")
            else:
                print(f"❌ 'model_path' is not string or None: {data['model_path']}")

            if isinstance(data["model_version"], str):
                print(f"✅ 'model_version' is string: {data['model_version']}")
            else:
                print(f"❌ 'model_version' is not string: {data['model_version']}")

            if isinstance(data["checksum"], str) or data["checksum"] is None:
                print(f"✅ 'checksum' is string or None: {data['checksum']}")
            else:
                print(f"❌ 'checksum' is not string or None: {data['checksum']}")

            if isinstance(data["load_time_seconds"], (int, float)) or data["load_time_seconds"] is None:
                print(f"✅ 'load_time_seconds' is numeric or None: {data['load_time_seconds']}")
            else:
                print(f"❌ 'load_time_seconds' is not numeric or None: {data['load_time_seconds']}")

            return True
    else:
        print(f"❌ Unexpected status code: {response.status_code}")
        print(f"Response text: {response.text}")
        return False

if __name__ == "__main__":
    success = test_model_info_endpoint()
    if success:
        print("\n🎉 Endpoint test passed!")
    else:
        print("\n💥 Endpoint test failed!")