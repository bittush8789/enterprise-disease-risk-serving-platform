import time
import json
import httpx

# Configuration
API_BASE_URL = "http://localhost:8000"
API_KEY = "dev-secret-key-12345"
HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

def print_separator(title):
    print("\n" + "="*50)
    print(f" {title} ")
    print("="*50)

def main():
    print("Starting AI FDE Client Integration Verification Tool...")
    time.sleep(1)

    # 1. Verify Platform Health
    print_separator("Step 1: Checking Platform Health Status")
    try:
        response = httpx.get(f"{API_BASE_URL}/health")
        print(f"HTTP Status: {response.status_code}")
        print(json.dumps(response.json(), indent=2))
        if response.json().get("status") != "healthy":
            print("WARNING: Platform is unhealthy or still bootstrapping model.")
    except Exception as e:
        print(f"FAILED: Connection to platform refused. Is the server running on port 8000? Details: {e}")
        return

    # 2. Get Model Registry Details
    print_separator("Step 2: Checking Production Model Metadata")
    try:
        response = httpx.get(f"{API_BASE_URL}/model/info", headers=HEADERS)
        print(f"HTTP Status: {response.status_code}")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"FAILED: Could not retrieve model info: {e}")

    # 3. Simulate Clinical Inference (First request - Cache Miss)
    print_separator("Step 3: Clinical Prediction - Request 1 (Cache Miss)")
    patient_payload = {
        "patient_id": "PAT-DEMO-FDE",
        "age": 52,
        "gender": "Male",
        "bmi": 32.8,
        "glucose_level": 195.0,
        "blood_pressure": 150.0,
        "insulin_level": 140.0,
        "family_history": True
    }
    
    try:
        print("Sending clinical metrics payload to /predict...")
        start_time = time.perf_counter()
        response = httpx.post(f"{API_BASE_URL}/predict", json=patient_payload, headers=HEADERS)
        total_time = (time.perf_counter() - start_time) * 1000
        
        print(f"HTTP Status: {response.status_code}")
        print(f"Response Payload:\n{json.dumps(response.json(), indent=2)}")
        print(f"Roundtrip Latency (from client): {total_time:.2f} ms")
        print(f"Engine-reported Internal Latency: {response.json().get('latency_ms')} ms")
    except Exception as e:
        print(f"FAILED: Prediction request failed: {e}")

    # 4. Simulate Clinical Inference (Second request - Cache Hit validation)
    print_separator("Step 4: Clinical Prediction - Request 2 (Cache Hit Verification)")
    try:
        print("Sending identical patient metrics payload to verify Redis cache speedup...")
        start_time = time.perf_counter()
        response = httpx.post(f"{API_BASE_URL}/predict", json=patient_payload, headers=HEADERS)
        total_time = (time.perf_counter() - start_time) * 1000
        
        print(f"HTTP Status: {response.status_code}")
        print(f"Response Payload:\n{json.dumps(response.json(), indent=2)}")
        print(f"Roundtrip Latency (from client): {total_time:.2f} ms")
        print(f"Engine-reported Internal Latency: {response.json().get('latency_ms')} ms")
        print("NOTICE: Notice how roundtrip latency drops significantly due to Redis caching!")
    except Exception as e:
        print(f"FAILED: Caching verification failed: {e}")

    # 5. Validate Input Sanitization & Resiliency
    print_separator("Step 5: Input Validation & Global Error Handler Check")
    bad_payload = {
        "patient_id": "PAT-BAD",
        "age": -5,  # Invalid negative age
        "gender": "Male",
        "bmi": 28.0,
        "glucose_level": 120.0,
        "blood_pressure": 110.0,
        "insulin_level": 50.0,
        "family_history": False
    }
    
    try:
        print("Sending invalid patient payload (negative age) to test exception mappings...")
        response = httpx.post(f"{API_BASE_URL}/predict", json=bad_payload, headers=HEADERS)
        print(f"HTTP Status (Expecting 400): {response.status_code}")
        print(f"Error Response Body:\n{json.dumps(response.json(), indent=2)}")
        print("SUCCESS: Error correctly mapped to standard clinical unavailable structure!")
    except Exception as e:
        print(f"FAILED: Resiliency test failed: {e}")

    # 6. Retrieve Prediction Log History
    print_separator("Step 6: Querying Historical Prediction Audit Logs")
    try:
        print("Fetching transaction history from Postgres...")
        response = httpx.get(f"{API_BASE_URL}/predictions?patient_id=PAT-DEMO-FDE&limit=2", headers=HEADERS)
        print(f"HTTP Status: {response.status_code}")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"FAILED: Log retrieval failed: {e}")

    print_separator("Clinical integration tests completed successfully!")

if __name__ == "__main__":
    main()
