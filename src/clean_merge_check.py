import sys
import json
import argparse


def ping():
    return "ok"


def check_clean_merge(cleaned, merged, key):
    """
    Compare two collections of records by identifier key.
    
    Args:
        cleaned: dict mapping identifiers to cleaned records
        merged: dict mapping identifiers to merged records
        key: name of the identifier field in records
    
    Returns:
        list of mismatch dicts, each containing:
            - 'key': the identifier value (or None if missing_key)
            - 'reason': one of 'missing_in_merged', 'missing_in_cleaned', 
                       'value_mismatch', 'missing_key'
    """
    mismatches = []
    
    # Get all unique identifiers from both sides
    all_ids = set(cleaned.keys()) | set(merged.keys())
    
    for record_id in all_ids:
        # Check if missing from merged
        if record_id not in merged:
            mismatches.append({
                'key': record_id,
                'reason': 'missing_in_merged'
            })
            continue
        
        # Check if missing from cleaned
        if record_id not in cleaned:
            mismatches.append({
                'key': record_id,
                'reason': 'missing_in_cleaned'
            })
            continue
        
        # Both present - check for missing key field
        cleaned_record = cleaned[record_id]
        merged_record = merged[record_id]
        
        if key not in cleaned_record or key not in merged_record:
            mismatches.append({
                'key': None,
                'reason': 'missing_key'
            })
            continue
        
        # Compare records
        if cleaned_record != merged_record:
            mismatches.append({
                'key': record_id,
                'reason': 'value_mismatch'
            })
    
    return mismatches


def main():
    """CLI entry point for clean/merge validation."""
    parser = argparse.ArgumentParser(
        description='Validate cleaned data matches merged data'
    )
    parser.add_argument('cleaned_file', help='Path to cleaned data JSON file')
    parser.add_argument('merged_file', help='Path to merged data JSON file')
    parser.add_argument('--key', default='id', help='Identifier field name (default: id)')
    
    args = parser.parse_args()
    
    # Load input files
    try:
        with open(args.cleaned_file, 'r') as f:
            cleaned = json.load(f)
        with open(args.merged_file, 'r') as f:
            merged = json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        print(f"Error loading input files: {e}", file=sys.stderr)
        sys.exit(2)
    
    # Run validation
    mismatches = check_clean_merge(cleaned, merged, args.key)
    
    # Report results
    if mismatches:
        for mismatch in mismatches:
            print(f"{mismatch['key']}: {mismatch['reason']}", file=sys.stderr)
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()

