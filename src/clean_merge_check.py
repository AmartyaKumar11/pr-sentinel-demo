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
            - 'id': the identifier value
            - 'reason': one of 'missing_in_merged', 'missing_in_cleaned', 
                       'value_mismatch', 'missing_key'
            - 'details': optional additional info
    """
    mismatches = []
    
    # Check for records missing key field in cleaned
    for record_id, record in cleaned.items():
        if key not in record:
            mismatches.append({
                'id': record_id,
                'reason': 'missing_key',
                'details': f'Record in cleaned missing key field "{key}"'
            })
    
    # Check for records missing key field in merged
    for record_id, record in merged.items():
        if key not in record:
            mismatches.append({
                'id': record_id,
                'reason': 'missing_key',
                'details': f'Record in merged missing key field "{key}"'
            })
    
    # Get all unique identifiers from both sides
    cleaned_ids = set(cleaned.keys())
    merged_ids = set(merged.keys())
    
    # Check for records missing in merged
    for record_id in cleaned_ids - merged_ids:
        mismatches.append({
            'id': record_id,
            'reason': 'missing_in_merged',
            'details': f'Record present in cleaned but absent in merged'
        })
    
    # Check for records missing in cleaned
    for record_id in merged_ids - cleaned_ids:
        mismatches.append({
            'id': record_id,
            'reason': 'missing_in_cleaned',
            'details': f'Record present in merged but absent in cleaned'
        })
    
    # Compare records present in both
    for record_id in cleaned_ids & merged_ids:
        cleaned_record = cleaned[record_id]
        merged_record = merged[record_id]
        
        # Skip if either has missing key field (already reported)
        if key not in cleaned_record or key not in merged_record:
            continue
        
        if cleaned_record != merged_record:
            mismatches.append({
                'id': record_id,
                'reason': 'value_mismatch',
                'details': f'Record values differ between cleaned and merged'
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
        print(f"Found {len(mismatches)} mismatch(es):", file=sys.stderr)
        for mismatch in mismatches:
            print(f"  ID {mismatch['id']}: {mismatch['reason']} - {mismatch['details']}", 
                  file=sys.stderr)
        sys.exit(1)
    else:
        print("Validation passed: cleaned and merged data match")
        sys.exit(0)


if __name__ == "__main__":
    main()

