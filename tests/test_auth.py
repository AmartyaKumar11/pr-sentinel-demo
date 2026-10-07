from src.auth import validate_token, hash_password, generate_reset_token
import src.auth
import base64
import json
import time


def _make_valid_token(user_id="userid123", exp_offset=3600):
    """Helper to create a valid token with proper exp claim."""
    payload = {"exp": time.time() + exp_offset}
    payload_json = json.dumps(payload)
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode()).decode().rstrip("=")
    return f"header.{payload_b64}.signature"


def test_validate_token_valid():
    result = validate_token(_make_valid_token())
    assert result["valid"] is True

def test_validate_token_invalid():
    try:
        validate_token("")
    except ValueError:
        pass

def test_hash_password():
    hashed, salt = hash_password("mypassword")
    assert len(hashed) == 64
    assert len(salt) == 32

def test_generate_reset_token():
    token = generate_reset_token("user-1")
    assert len(token) > 20


def test_validate_email_format_before_sending_reset():
    """Test that invalid emails are rejected before token generation."""
    from unittest.mock import patch
    from src.auth import reset_password, _reset_tokens
    
    invalid_emails = ["not-an-email", "a@b", "", None]
    
    with patch('src.notifications.send_email') as mock_send:
        mock_send.side_effect = Exception("send_email should not be called")
        
        for email in invalid_emails:
            _reset_tokens.clear()
            result = reset_password(email)
            
            assert result["status"] == "error"
            assert result["error"] == "invalid_email"
            assert len(_reset_tokens) == 0
        
        mock_send.assert_not_called()


def test_send_reset_email_with_token():
    from unittest.mock import patch
    from src.auth import reset_password, validate_reset_token, _reset_tokens
    
    _reset_tokens.clear()
    
    with patch('src.notifications.send_email') as mock_send:
        result = reset_password("user@example.com")
        
        assert result["status"] == "sent"
        assert "token" not in result
        
        mock_send.assert_called_once()
        call_args = mock_send.call_args[0]
        assert call_args[0] == "user@example.com"
        
        assert len(_reset_tokens) == 1
        token = list(_reset_tokens.keys())[0]
        
        validate_result = validate_reset_token(token)
        assert validate_result["status"] == "ok"
        assert validate_result["email"] == "user@example.com"


def test_expire_token_after_1_hour():
    from unittest.mock import patch
    from datetime import datetime, timedelta, timezone
    from src.auth import reset_password, validate_reset_token, _reset_tokens
    
    _reset_tokens.clear()
    
    with patch('src.notifications.send_email'):
        result = reset_password("user@example.com")
        assert result["status"] == "sent"
    
    token = list(_reset_tokens.keys())[0]
    
    future_time = datetime.now(timezone.utc) + timedelta(hours=1, minutes=1)
    
    with patch('src.auth.datetime') as mock_datetime:
        mock_datetime.now.return_value = future_time
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
        
        validate_result = validate_reset_token(token)
        assert validate_result["status"] == "error"
        assert validate_result["error"] == "expired_token"


def test_reset_token_first_use_succeeds():
    from unittest.mock import patch
    from src.auth import reset_password, validate_reset_token, _reset_tokens
    
    _reset_tokens.clear()
    
    with patch('src.notifications.send_email') as mock_send:
        result = reset_password("user@example.com")
        assert result["status"] == "sent"
        
        call_args = mock_send.call_args[0]
        token = call_args[2].split(": ")[1]
        
        validate_result = validate_reset_token(token)
        assert validate_result["status"] == "ok"
        assert validate_result["email"] == "user@example.com"


def test_reset_token_second_use_rejected():
    """Test that a token can only be used once."""
    from unittest.mock import patch
    from src.auth import reset_password, validate_reset_token, _reset_tokens
    
    _reset_tokens.clear()
    
    with patch('src.notifications.send_email') as mock_send:
        result = reset_password("user@example.com")
        assert result["status"] == "sent"
        
        call_args = mock_send.call_args[0]
        token = call_args[2].split(": ")[1]
        
        first_result = validate_reset_token(token)
        assert first_result["status"] == "ok"
        
        second_result = validate_reset_token(token)
        assert second_result["status"] == "error"
        assert second_result["error"] == "invalid_token"


def test_reset_token_expired_rejected():
    """Test that expired tokens are rejected."""
    from unittest.mock import patch
    from datetime import datetime, timedelta, timezone
    from src.auth import reset_password, validate_reset_token, _reset_tokens
    
    _reset_tokens.clear()
    
    with patch('src.notifications.send_email'):
        result = reset_password("user@example.com")
        assert result["status"] == "sent"
    
    token = list(_reset_tokens.keys())[0]
    _reset_tokens[token]["expires_at"] = datetime.now(timezone.utc) - timedelta(seconds=1)
    
    validate_result = validate_reset_token(token)
    assert validate_result["status"] == "error"
    assert validate_result["error"] == "expired_token"
    assert token not in _reset_tokens


def test_reset_token_malformed_rejected():
    """Test that malformed tokens are rejected."""
    from src.auth import validate_reset_token
    
    invalid_tokens = ["", None, "garbage", "not-a-real-token"]
    
    for token in invalid_tokens:
        result = validate_reset_token(token)
        assert result["status"] == "error"
        assert result["error"] == "invalid_token"


def test_reset_token_concurrent_replay():
    """Test that concurrent token validation attempts are handled safely."""
    from unittest.mock import patch
    from concurrent.futures import ThreadPoolExecutor
    from src.auth import reset_password, validate_reset_token, _reset_tokens
    
    _reset_tokens.clear()
    
    with patch('src.notifications.send_email') as mock_send:
        result = reset_password("user@example.com")
        assert result["status"] == "sent"
        
        call_args = mock_send.call_args[0]
        token = call_args[2].split(": ")[1]
        
        with ThreadPoolExecutor(max_workers=2) as executor:
            future1 = executor.submit(validate_reset_token, token)
            future2 = executor.submit(validate_reset_token, token)
            
            result1 = future1.result()
            result2 = future2.result()
        
        results = [result1, result2]
        ok_results = [r for r in results if r["status"] == "ok"]
        error_results = [r for r in results if r["status"] == "error"]
        
        assert len(ok_results) == 1
        assert len(error_results) == 1
        assert ok_results[0]["email"] == "user@example.com"


def test_reject_expired_tokens():
    """Test that expired tokens are rejected."""
    import base64
    import json
    import time
    
    payload = {"exp": time.time() - 3600}
    payload_json = json.dumps(payload)
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode()).decode().rstrip("=")
    token = f"header.{payload_b64}.signature"
    
    try:
        validate_token(token)
        assert False, "Expected ValueError for expired token"
    except ValueError as e:
        assert "expired" in str(e).lower()


def test_reject_missing_exp():
    """Test that tokens without exp claim are rejected."""
    import base64
    import json
    
    payload = {"sub": "user123"}
    payload_json = json.dumps(payload)
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode()).decode().rstrip("=")
    token = f"header.{payload_b64}.signature"
    
    try:
        validate_token(token)
        assert False, "Expected ValueError for missing exp"
    except ValueError as e:
        assert "missing expiration" in str(e).lower()


def test_accept_valid_token():
    """Test that valid tokens with future exp are accepted."""
    import base64
    import json
    import time
    
    payload = {"exp": time.time() + 3600}
    payload_json = json.dumps(payload)
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode()).decode().rstrip("=")
    token = f"header.{payload_b64}.signature"
    
    result = validate_token(token)
    assert result["valid"] is True
    assert result["user_id"] == payload_b64


def test_reject_malformed_signature_still_works():
    """Test that short signatures are still rejected before expiration check."""
    import base64
    import json
    import time
    
    payload = {"exp": time.time() + 3600}
    payload_json = json.dumps(payload)
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode()).decode().rstrip("=")
    token = f"header.{payload_b64}.short"
    
    try:
        validate_token(token)
        assert False, "Expected ValueError for malformed signature"
    except ValueError as e:
        assert "malformed signature" in str(e).lower()


def test_check_permissions_rejects_empty_user_id():
    """Test that check_permissions raises ValueError for empty user_id."""
    from src.auth import check_permissions
    
    try:
        check_permissions("", "repo:123")
        assert False, "Expected ValueError for empty user_id"
    except ValueError as e:
        assert "user_id" in str(e).lower()


def test_check_permissions_rejects_empty_resource():
    """Test that check_permissions raises ValueError for empty resource."""
    from src.auth import check_permissions
    
    try:
        check_permissions("user-1", "")
        assert False, "Expected ValueError for empty resource"
    except ValueError as e:
        assert "resource" in str(e).lower()


def test_check_permissions_rejects_resource_without_colon():
    """Test that check_permissions raises ValueError for resource without namespace colon."""
    from src.auth import check_permissions
    
    try:
        check_permissions("user-1", "repo123")
        assert False, "Expected ValueError for resource without colon"
    except ValueError as e:
        assert "namespaced" in str(e).lower() or ":" in str(e)


def test_check_permissions_accepts_valid_namespaced_resource():
    """Test that check_permissions returns True for valid namespaced resource."""
    from src.auth import check_permissions
    
    result = check_permissions("user-1", "repo:123")
    assert result is True


def test_check_permissions_does_not_raise_on_valid_input():
    """Test that check_permissions does not raise for valid input."""
    from src.auth import check_permissions
    
    check_permissions("user-1", "repo:123")
    check_permissions("admin", "dashboard:read")
    check_permissions("user-42", "profile:write")


def test_validate_token_accepts_unexpired_token():
    """Test that validate_token accepts tokens with future expiration."""
    now = time.time()
    payload = {"exp": now + 60}
    payload_json = json.dumps(payload)
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode()).decode().rstrip("=")
    token = f"header.{payload_b64}.signature"
    
    result = validate_token(token)
    assert result["valid"] is True
    assert result["user_id"] == payload_b64


def test_validate_token_rejects_expired_token():
    """Test that validate_token rejects tokens with past expiration."""
    now = time.time()
    payload = {"exp": now - 3600}
    payload_json = json.dumps(payload)
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode()).decode().rstrip("=")
    token = f"header.{payload_b64}.signature"
    
    try:
        validate_token(token)
        assert False, "Expected ValueError for expired token"
    except ValueError as e:
        assert str(e) == "Token expired"


def test_validate_token_respects_clock_skew():
    """Test that validate_token respects CLOCK_SKEW_SECONDS."""
    now = time.time()
    
    payload_within_skew = {"exp": now - (src.auth.CLOCK_SKEW_SECONDS - 1)}
    payload_json = json.dumps(payload_within_skew)
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode()).decode().rstrip("=")
    token_within = f"header.{payload_b64}.signature"
    
    result = validate_token(token_within)
    assert result["valid"] is True
    
    payload_outside_skew = {"exp": now - (src.auth.CLOCK_SKEW_SECONDS + 1)}
    payload_json = json.dumps(payload_outside_skew)
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode()).decode().rstrip("=")
    token_outside = f"header.{payload_b64}.signature"
    
    try:
        validate_token(token_outside)
        assert False, "Expected ValueError for token outside clock skew"
    except ValueError as e:
        assert str(e) == "Token expired"
