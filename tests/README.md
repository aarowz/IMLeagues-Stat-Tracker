# Tests Directory

This directory contains integration tests for the IMLeagues Stat Tracker application.

## Files

- **`test_quick.py`** - Quick connectivity test to verify all API endpoints are accessible
- **`test_integration.py`** - Comprehensive integration test suite (46 tests)
- **`TESTING.md`** - Complete testing documentation and guide

## Running Tests

### Quick Connectivity Test
```bash
python3 tests/test_quick.py
```

### Full Integration Test Suite
```bash
python3 tests/test_integration.py
```

Or from the project root:
```bash
cd tests && python3 test_quick.py
cd tests && python3 test_integration.py
```

## Test Coverage

The integration tests cover:
- ✅ System Admin API endpoints (20 tests)
- ✅ Player API endpoints (16 tests)
- ✅ Stat Keeper API endpoints (5 tests)
- ✅ Team Captain API endpoints (3 tests)
- ✅ Data consistency checks (2 tests)

**Total: 46 tests**

## Prerequisites

1. Docker containers must be running: `docker compose up -d`
2. API must be accessible at `http://localhost:4000`
3. Database must be initialized
4. Python `requests` library installed

See `TESTING.md` for detailed documentation.

