import pytest
import sys
import json
import tempfile
import subprocess
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from clean_merge_check import ping, check_clean_merge, main


def test_ping_still_returns_ok():
    """Ensure ping() function still works as originally defined."""
    assert ping() == "ok"


def test_check_clean_merge_identical():
    """Identical cleaned and merged dicts should produce no mismatches."""
    cleaned = {
        '1': {'id': '1', 'name': 'Alice', 'value': 100},
        '2': {'id': '2', 'name': 'Bob', 'value': 200}
    }
    merged = {
        '1': {'id': '1', 'name': 'Alice', 'value': 100},
        '2': {'id': '2', 'name': 'Bob', 'value': 200}
    }
    
    result = check_clean_merge(cleaned, merged, 'id')
    assert len(result) == 0, "Identical data should produce no mismatches"


def test_check_clean_merge_value_mismatch():
    """One differing record should produce exactly one value_mismatch."""
    cleaned = {
        '1': {'id': '1', 'name': 'Alice', 'value': 100},
        '2': {'id': '2', 'name': 'Bob', 'value': 200}
    }
    merged = {
        '1': {'id': '1', 'name': 'Alice', 'value': 100},
        '2': {'id': '2', 'name': 'Bob', 'value': 999}  # Different value
    }
    
    result = check_clean_merge(cleaned, merged, 'id')
    assert len(result) == 1, "Should detect exactly one mismatch"
    assert result[0]['id'] == '2', "Mismatch should have correct identifier"
    assert result[0]['reason'] == 'value_mismatch', "Should report value_mismatch"


def test_check_clean_merge_missing_in_merged():
    """Record in cleaned but not merged should be reported."""
    cleaned = {
        '1': {'id': '1', 'name': 'Alice'},
        '2': {'id': '2', 'name': 'Bob'}
    }
    merged = {
        '1': {'id': '1', 'name': 'Alice'}
        # Record '2' is missing
    }
    
    result = check_clean_merge(cleaned, merged, 'id')
    assert len(result) == 1, "Should detect one missing record"
    assert result[0]['id'] == '2', "Should identify missing record by ID"
    assert result[0]['reason'] == 'missing_in_merged'


def test_check_clean_merge_missing_in_cleaned():
    """Record in merged but not cleaned should be reported."""
    cleaned = {
        '1': {'id': '1', 'name': 'Alice'}
    }
    merged = {
        '1': {'id': '1', 'name': 'Alice'},
        '2': {'id': '2', 'name': 'Bob'}  # Extra record
    }
    
    result = check_clean_merge(cleaned, merged, 'id')
    assert len(result) == 1, "Should detect one extra record"
    assert result[0]['id'] == '2', "Should identify extra record by ID"
    assert result[0]['reason'] == 'missing_in_cleaned'


def test_check_clean_merge_missing_key_field():
    """Record lacking the key field should be reported, not crash."""
    cleaned = {
        '1': {'id': '1', 'name': 'Alice'},
        '2': {'name': 'Bob'}  # Missing 'id' field
    }
    merged = {
        '1': {'id': '1', 'name': 'Alice'},
        '2': {'id': '2', 'name': 'Bob'}
    }
    
    result = check_clean_merge(cleaned, merged, 'id')
    
    # Should report missing_key, not crash
    missing_key_errors = [m for m in result if m['reason'] == 'missing_key']
    assert len(missing_key_errors) >= 1, "Should detect missing key field"
    assert any(m['id'] == '2' for m in missing_key_errors), "Should identify record with missing key"


def test_main_exits_nonzero_on_mismatch(tmp_path):
    """CLI should exit 1 when mismatches are found."""
    cleaned_file = tmp_path / "cleaned.json"
    merged_file = tmp_path / "merged.json"
    
    cleaned_data = {
        '1': {'id': '1', 'name': 'Alice', 'value': 100}
    }
    merged_data = {
        '1': {'id': '1', 'name': 'Alice', 'value': 999}  # Mismatch
    }
    
    cleaned_file.write_text(json.dumps(cleaned_data))
    merged_file.write_text(json.dumps(merged_data))
    
    result = subprocess.run(
        [sys.executable, 'src/clean_merge_check.py', 
         str(cleaned_file), str(merged_file)],
        capture_output=True,
        cwd=Path(__file__).parent.parent
    )
    
    assert result.returncode == 1, "Should exit with code 1 on mismatch"
    assert b"mismatch" in result.stderr.lower(), "Should report mismatch to stderr"


def test_main_exits_zero_when_clean(tmp_path):
    """CLI should exit 0 when data matches."""
    cleaned_file = tmp_path / "cleaned.json"
    merged_file = tmp_path / "merged.json"
    
    data = {
        '1': {'id': '1', 'name': 'Alice', 'value': 100},
        '2': {'id': '2', 'name': 'Bob', 'value': 200}
    }
    
    cleaned_file.write_text(json.dumps(data))
    merged_file.write_text(json.dumps(data))
    
    result = subprocess.run(
        [sys.executable, 'src/clean_merge_check.py', 
         str(cleaned_file), str(merged_file)],
        capture_output=True,
        cwd=Path(__file__).parent.parent
    )
    
    assert result.returncode == 0, "Should exit with code 0 when data matches"
