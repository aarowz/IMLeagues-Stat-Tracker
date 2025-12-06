#!/usr/bin/env python3
"""
Quick Connectivity Test - Verifies API is running and accessible
Run this first before running the full integration test suite
"""

import requests
import sys

API_BASE = "http://localhost:4000"

def test_connectivity():
    """Test basic API connectivity"""
    print("Testing API Connectivity...")
    print("-" * 50)
    
    endpoints = [
        ("System Admin", f"{API_BASE}/system-admin/sports"),
        ("Player", f"{API_BASE}/player/players"),
        ("Stat Keeper", f"{API_BASE}/stat-keeper/stat-keepers/1/games"),
        ("Team Captain", f"{API_BASE}/team-captain/teams/1/games"),
    ]
    
    all_passed = True
    
    for name, url in endpoints:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code in [200, 404]:  # 404 is OK, means endpoint exists
                print(f"✅ {name}: Connected (Status {response.status_code})")
            else:
                print(f"⚠️  {name}: Status {response.status_code}")
                all_passed = False
        except requests.exceptions.ConnectionError:
            print(f"❌ {name}: Connection failed - Is the API running?")
            print(f"   Try: docker compose up -d")
            all_passed = False
        except Exception as e:
            print(f"❌ {name}: Error - {str(e)}")
            all_passed = False
    
    print("-" * 50)
    
    if all_passed:
        print("✅ All endpoints are accessible!")
        print("\nYou can now run the full integration test:")
        print("   python3 tests/test_integration.py")
        print("   (or: cd tests && python3 test_integration.py)")
        return True
    else:
        print("❌ Some endpoints are not accessible.")
        print("\nPlease ensure:")
        print("1. Docker containers are running: docker compose up -d")
        print("2. API is accessible at http://localhost:4000")
        print("3. Database is initialized")
        return False

if __name__ == "__main__":
    success = test_connectivity()
    sys.exit(0 if success else 1)

