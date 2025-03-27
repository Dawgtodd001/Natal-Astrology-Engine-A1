#!/usr/bin/env python3
"""
Test script to verify Redis cache functionality
"""
import json
import sys
import time
import requests
from datetime import datetime

# Define API base URL
API_URL = "http://localhost:8000/api"
CACHE_URL = f"{API_URL}/cache"

def test_redis_health():
    """Test Redis health endpoint"""
    print("Testing Redis health...")
    try:
        response = requests.get(f"{CACHE_URL}/health")
        data = response.json()
        
        if response.status_code == 200:
            print(f"✅ Redis health check: {data}")
        else:
            print(f"❌ Redis health check failed: {response.status_code}")
            print(response.text)
        
        return data.get("available", False)
    except Exception as e:
        print(f"❌ Redis health check error: {str(e)}")
        return False

def test_redis_stats(admin_password):
    """Test Redis stats endpoint"""
    print("\nTesting Redis stats...")
    try:
        response = requests.get(f"{CACHE_URL}/stats", params={"admin_password": admin_password})
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Redis stats retrieved successfully")
            print(f"  - Available: {data['available']}")
            print(f"  - Keys count: {data['keys_count']}")
            print(f"  - Memory used: {data['memory_used']}")
            print(f"  - Hit rate: {data.get('hit_rate', 'N/A')}%")
            print(f"  - Uptime: {data.get('uptime', 'N/A')}")
        else:
            print(f"❌ Redis stats check failed: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Redis stats check error: {str(e)}")

def test_cached_chart_calculation():
    """Test cached chart calculation with two identical requests"""
    print("\nTesting chart calculation caching...")
    
    # Define test chart parameters
    chart_params = {
        "birth_date": "1990-01-01",
        "birth_time": "12:00",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "timezone": "America/New_York",
        "house_system": "placidus",
        "zodiac_type": "tropical"
    }
    
    # First request - should be a cache miss
    try:
        start_time = time.time()
        response1 = requests.post(f"{API_URL}/chart", json=chart_params)
        duration1 = time.time() - start_time
        
        if response1.status_code == 200:
            data1 = response1.json()
            cache_hit1 = data1.get("_cache_hit", False)
            print(f"✅ First chart request succeeded in {duration1:.3f}s (Cache hit: {cache_hit1})")
        else:
            print(f"❌ First chart request failed: {response1.status_code}")
            print(response1.text)
            return
    except Exception as e:
        print(f"❌ First chart request error: {str(e)}")
        return
    
    # Second request with same parameters - should be a cache hit
    try:
        # Small delay to ensure we can clearly see timing difference
        time.sleep(1)
        
        start_time = time.time()
        response2 = requests.post(f"{API_URL}/chart", json=chart_params)
        duration2 = time.time() - start_time
        
        if response2.status_code == 200:
            data2 = response2.json()
            cache_hit2 = data2.get("_cache_hit", False)
            print(f"✅ Second chart request succeeded in {duration2:.3f}s (Cache hit: {cache_hit2})")
            
            # Check if second request was faster (cache hit)
            if duration2 < duration1:
                print(f"✅ Cache improved performance by {(duration1-duration2)/duration1*100:.1f}%")
            else:
                print("⚠️ Second request wasn't faster - cache might not be working")
        else:
            print(f"❌ Second chart request failed: {response2.status_code}")
            print(response2.text)
    except Exception as e:
        print(f"❌ Second chart request error: {str(e)}")

def test_redis_keys(admin_password):
    """Test Redis keys endpoint"""
    print("\nTesting Redis keys...")
    try:
        response = requests.get(
            f"{CACHE_URL}/keys", 
            params={"admin_password": admin_password, "pattern": "astro_chart:*", "limit": 5}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Redis keys retrieved successfully, found {len(data)} keys")
            for i, key_info in enumerate(data[:3], 1):
                print(f"  {i}. {key_info['key']} (TTL: {key_info['ttl']}s, Size: {key_info['size']} bytes)")
                if key_info.get('sample'):
                    sample = key_info['sample']
                    if len(sample) > 50:
                        sample = sample[:50] + "..."
                    print(f"     Sample: {sample}")
        else:
            print(f"❌ Redis keys check failed: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Redis keys check error: {str(e)}")

def main():
    """Main test function"""
    print("=== Redis Cache Integration Test ===")
    print(f"Testing against API: {API_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 40)
    
    # Admin password for protected endpoints
    admin_password = "natal_admin_2025"  # Default development password
    
    # Check if Redis is available
    redis_available = test_redis_health()
    
    if not redis_available:
        print("\n❌ Redis is not available. Skipping remaining tests.")
        return
    
    # Run cache tests
    test_redis_stats(admin_password)
    test_cached_chart_calculation()
    test_redis_keys(admin_password)
    
    print("\n=== Test Completed ===")

if __name__ == "__main__":
    main()