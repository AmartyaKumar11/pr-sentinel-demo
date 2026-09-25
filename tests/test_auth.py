from src.auth import validate_token, hash_password, generate_reset_token

def test_validate_token_valid():
    result = validate_token("header.userid123.signature")
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
    from unittest.mock import patch
    from src.auth import reset_password, _reset_tokens
    
    with patch('src.notifications.send_email') as mock_send:
        result = reset_password("not-an-email")
        
        assert result["status"] == "error"
        assert result["error"] == "invalid_email"
        mock_send.assert_not_called()
        assert len(_reset_tokens) == 0


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
    from src.auth import validate_reset_token
    
    result = validate_reset_token("not-a-real-token")
    assert result["status"] == "error"
    assert result["error"] == "invalid_token"


def test_reset_token_concurrent_replay():
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
