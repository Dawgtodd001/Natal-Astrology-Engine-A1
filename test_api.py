#!/usr/bin/env python
"""
Test script for the Natal Astrology API endpoints
"""
import json
import subprocess
import sys

def run_curl_command(endpoint, data=None, method="GET", api_key=None):
    """Run a curl command and return the parsed JSON response"""
    cmd = ["curl", f"http://localhost:8000{endpoint}"]
    
    if method != "GET":
        cmd.extend(["-X", method])
    
    cmd.extend(["-H", "Content-Type: application/json"])
    
    if api_key:
        cmd.extend(["-H", f"X-API-Key: {api_key}"])
        
    if data:
        cmd.extend(["-d", json.dumps(data)])
    
    print(f"Running: {' '.join(cmd)}")
    process = subprocess.run(cmd, capture_output=True, text=True)
    
    print(f"Status code: {process.returncode}")
    
    if process.returncode != 0:
        print("Error response:", process.stderr)
        return None
    
    try:
        return json.loads(process.stdout)
    except json.JSONDecodeError:
        print("Invalid JSON response:", process.stdout[:200])
        return process.stdout

def test_health_endpoint():
    """Test the health endpoint"""
    print("\n=== Testing /api/health endpoint ===")
    response = run_curl_command("/api/health")
    
    if response and isinstance(response, dict) and response.get("status") == "healthy":
        print("Health check passed")
        return True
    else:
        print("Health check failed")
        return False

def test_chart_generation():
    """Test the chart generation endpoint"""
    print("\n=== Testing /api/chart endpoint ===")
    
    data = {
        "birth_date": "1990-01-01",
        "birth_time": "12:00",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "timezone": "America/New_York",
        "house_system": "placidus",
        "zodiac_type": "tropical"
    }
    
    response = run_curl_command("/api/chart", data=data, method="POST", api_key="test_key_1234567890")
    
    if response and isinstance(response, dict) and "planets" in response:
        print("Chart generation test passed")
        # Print a few planets as a sample
        for planet in response.get("planets", [])[:3]:
            print(f"{planet['name']} in {planet['sign']} (House {planet['house']})")
        return True
    else:
        print("Chart generation test failed")
        return False

def test_chart_interpretation():
    """Test the chart interpretation endpoint"""
    print("\n=== Testing /api/interpret endpoint ===")
    
    data = {
        "birth_date": "1990-01-01",
        "birth_time": "12:00",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "timezone": "America/New_York",
        "house_system": "placidus",
        "zodiac_type": "tropical",
        "template_name": "basic_text"
    }
    
    response = run_curl_command("/api/interpret", data=data, method="POST", api_key="test_key_1234567890")
    
    if response and isinstance(response, str) and "Natal Chart Interpretation" in response:
        print("Chart interpretation test passed")
        # Print first few lines of interpretation
        print(response.split("\n")[:5])
        return True
    else:
        print("Chart interpretation test failed")
        return False

def test_house_systems():
    """Test the house systems endpoint"""
    print("\n=== Testing /api/house-systems endpoint ===")
    
    response = run_curl_command("/api/house-systems", method="GET", api_key="test_key_1234567890")
    
    if response and isinstance(response, dict) and len(response) > 0:
        print("House systems test passed")
        print(f"Available house systems: {', '.join(list(response.keys())[:5])}...")
        return True
    else:
        print("House systems test failed")
        return False

def main():
    """Main test function"""
    print("Starting Natal Astrology API Tests\n")
    
    tests = [
        test_health_endpoint,
        test_chart_generation,
        test_chart_interpretation,
        test_house_systems
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    # Summary
    print("\n=== Test Summary ===")
    print(f"Tests passed: {results.count(True)}/{len(results)}")
    
    if all(results):
        print("\nAll tests passed successfully!")
        return 0
    else:
        print("\nSome tests failed. See details above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())