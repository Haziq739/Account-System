"""Auth test script."""
import sys
sys.path.insert(0, '.')
from services.auth import AuthService

def test_auth():
    # Test 1: Create user
    print("[TEST 1] Creating test user...")
    try:
        AuthService.create_user("testuser_x", "testx@example.com", "old123")
        print("  PASS: user created")
    except ValueError as e:
        print(f"  INFO: {e} (already exists, continuing)")

    # Test 2: Login correct
    print("[TEST 2] Login with correct password...")
    user = AuthService.login("testuser_x", "old123")
    assert user is not None, "FAIL: login returned None"
    print(f"  PASS: logged in as id={user['id']}")

    # Test 3: Login wrong password
    print("[TEST 3] Login with wrong password...")
    bad = AuthService.login("testuser_x", "wrongpass")
    assert bad is None, "FAIL: should return None"
    print("  PASS: wrong password rejected")

    # Test 4: Change password
    print("[TEST 4] Change password old123 -> new123...")
    ok = AuthService.change_password(user["id"], "old123", "new123")
    assert ok, "FAIL: change_password returned False"
    print("  PASS: password changed")

    # Test 5: Login with NEW password
    print("[TEST 5] Login with new password new123...")
    user2 = AuthService.login("testuser_x", "new123")
    assert user2 is not None, "FAIL: new password login failed"
    print("  PASS: new password works")

    # Test 6: Old password must fail
    print("[TEST 6] Old password must be rejected...")
    old_try = AuthService.login("testuser_x", "old123")
    assert old_try is None, "FAIL: old password still accepted"
    print("  PASS: old password rejected")

    # Test 7: Forgot password
    print("[TEST 7] Forgot password via email...")
    found = AuthService.verify_email("testx@example.com")
    assert found, "FAIL: email not found"
    ok2 = AuthService.reset_password("testx@example.com", "reset123")
    assert ok2, "FAIL: reset_password returned False"
    user3 = AuthService.login("testuser_x", "reset123")
    assert user3 is not None, "FAIL: login after reset failed"
    print("  PASS: reset + login works")

    print()
    print("All 7 auth tests PASSED.")

test_auth()
