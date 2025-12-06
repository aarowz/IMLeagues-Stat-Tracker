# Integration Testing Guide

This document describes how to run integration tests for the IMLeagues Stat Tracker application.

## Prerequisites

1. **Docker containers must be running:**
   ```bash
   docker compose up -d
   ```

2. **API must be accessible at `http://localhost:4000`**

3. **Database must be initialized** (should happen automatically on first run)

4. **Python requests library** (usually pre-installed, but if needed):
   ```bash
   pip install requests
   ```

## Quick Connectivity Test

Before running the full test suite, verify basic connectivity:

```bash
python3 tests/test_quick.py
```

Or from the tests directory:
```bash
cd tests && python3 test_quick.py
```

This will test:
- System Admin API endpoints
- Player API endpoints
- Stat Keeper API endpoints
- Team Captain API endpoints

## Full Integration Test Suite

Run the comprehensive integration test:

```bash
python3 tests/test_integration.py
```

Or from the tests directory:
```bash
cd tests && python3 test_integration.py
```

### What It Tests

The integration test suite covers:

#### System Admin (20 tests)
- ✅ GET endpoints for Sports, Leagues, Teams, Players, Games
- ✅ Analytics dashboard
- ✅ League teams, games, champions
- ✅ Team players, games, stats
- ✅ Player teams, games, stats
- ✅ Game details

#### Player (16 tests)
- ✅ Player profile and stats
- ✅ Player teams and games (upcoming/all)
- ✅ League teams, games, standings
- ✅ Team details, players, games, stats
- ✅ Analytics endpoints

#### Stat Keeper (5 tests)
- ✅ Assigned games
- ✅ Game details and players
- ✅ Stat events
- ✅ Game summary

#### Team Captain (3 tests)
- ✅ Team captain teams
- ✅ Team games and stats

#### Data Consistency (2 tests)
- ✅ League-Team relationships
- ✅ Game-Team relationships

**Total: 46 tests**

### Test Output

The test script will:
1. Display progress for each test
2. Show ✅ for passed tests
3. Show ❌ for failed tests with error details
4. Provide a summary at the end

### Example Output

```
================================================================================
IMLeagues Stat Tracker - Integration Test Suite
================================================================================

📊 SYSTEM ADMIN TESTS
--------------------------------------------------------------------------------
✅ PASS: System Admin: GET /sports
   Found 3 sports
✅ PASS: System Admin: GET /leagues
   Found 5 leagues
...

================================================================================
TEST SUMMARY
================================================================================
Total Tests: 46
✅ Passed: 46
❌ Failed: 0

🎉 All tests passed!
```

## Troubleshooting

### Connection Errors

If you see connection errors:
1. Check Docker containers: `docker compose ps`
2. Check API logs: `docker compose logs web-api`
3. Verify API is running: `curl http://localhost:4000/system-admin/sports`

### 500 Errors

If endpoints return 500 errors:
1. Check database connection: `docker compose logs mysql_db`
2. Verify database is initialized: Check for SQL execution logs
3. Check API logs for specific error messages

### Missing Data

If tests fail due to missing data:
1. Verify database has been populated with mock data
2. Check SQL files in `database-files/` directory
3. Recreate database: `docker compose down -v && docker compose up -d`

## Manual Testing

For manual testing of the Streamlit UI:

1. **Start the application:**
   ```bash
   docker compose up -d
   ```

2. **Access Streamlit UI:**
   - Open browser to `http://localhost:8501`

3. **Test each persona:**
   - System Admin: Click "Act as System Administrator"
   - Stat Keeper: Click "Act as Statkeeper"
   - Player: Click "Act as Player"
   - Team Captain: Click "Act as Team Captain"

4. **Test key workflows:**
   - System Admin: Create/update data, assign awards, view analytics
   - Stat Keeper: Log stats, finalize games, view assigned games
   - Player: View stats, browse games, explore teams/leagues
   - Team Captain: Schedule games, view team stats, compare performance

## Continuous Integration

For CI/CD pipelines, you can run:

```bash
# Quick connectivity check
python3 tests/test_quick.py || exit 1

# Full integration test
python3 tests/test_integration.py || exit 1
```

## Test Coverage

The integration tests verify:
- ✅ All REST API endpoints are accessible
- ✅ Data is returned in expected format
- ✅ Relationships between entities are consistent
- ✅ No critical errors occur during data retrieval
- ✅ Analytics endpoints return valid data

**Note:** These tests focus on integration and connectivity. For unit tests of individual functions, see the respective module test files.

