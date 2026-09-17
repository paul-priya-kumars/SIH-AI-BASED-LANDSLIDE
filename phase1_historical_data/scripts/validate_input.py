import pandas as pd
import argparse
from pathlib import Path
from datetime import datetime

def validate_landslide_csv(input_path):
    """
    Validate a CSV file containing historical landslide data.

    Args:
        input_path (str or Path): Path to the CSV file to validate.

    Returns:
        dict: Validation results.
    """
    # Convert to Path object
    input_path = Path(input_path)

    # Check if file exists
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # Read the CSV file
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        raise ValueError(f"Error reading CSV file: {e}")

    # Define field categories
    required_fields = ['landslide_id', 'date', 'latitude', 'longitude']
    recommended_fields = ['location', 'district', 'state', 'country', 'source', 'source_url']
    optional_fields = ['severity', 'description']

    # Initialize validation results
    validation_results = {
        'total_records': len(df),
        'valid_records': 0,
        'records_with_errors': 0,
        'records_with_warnings': 0,
        'duplicate_ids': 0,
        'missing_coordinates': 0,
        'invalid_coordinates': 0,
        'invalid_dates': 0,
        'missing_required_fields': {},
        'missing_recommended_fields': {},
        'error_details': [],
        'warning_details': []
    }

    # Track landslide IDs for duplicate detection
    seen_ids = set()
    duplicate_ids = set()

    # Validate each record
    for idx, row in df.iterrows():
        record_num = idx + 1  # 1-based for reporting
        has_error = False
        has_warning = False

        # Check required fields
        for field in required_fields:
            if field not in df.columns:
                validation_results['missing_required_fields'][field] = validation_results['missing_required_fields'].get(field, 0) + 1
                has_error = True
            elif pd.isna(row[field]) or (isinstance(row[field], str) and row[field].strip() == ''):
                validation_results['missing_required_fields'][field] = validation_results['missing_required_fields'].get(field, 0) + 1
                has_error = True

        # Check duplicate landslide_id
        if 'landslide_id' in df.columns and not pd.isna(row['landslide_id']):
            landslide_id = str(row['landslide_id']).strip()
            if landslide_id in seen_ids:
                duplicate_ids.add(landslide_id)
                has_error = True
                validation_results['error_details'].append(f"Record {record_num}: Duplicate landslide ID '{landslide_id}'")
            else:
                seen_ids.add(landslide_id)

        # Validate latitude
        if 'latitude' in df.columns and not pd.isna(row['latitude']):
            try:
                lat = float(row['latitude'])
                if lat < -90 or lat > 90:
                    validation_results['invalid_coordinates'] += 1
                    has_error = True
                    validation_results['error_details'].append(f"Record {record_num}: Invalid latitude {lat} (must be between -90 and 90)")
            except ValueError:
                validation_results['invalid_coordinates'] += 1
                has_error = True
                validation_results['error_details'].append(f"Record {record_num}: Invalid latitude value '{row['latitude']}'")
        elif 'latitude' in df.columns:
            validation_results['missing_coordinates'] += 1
            has_warning = True
            validation_results['warning_details'].append(f"Record {record_num}: Missing latitude")

        # Validate longitude
        if 'longitude' in df.columns and not pd.isna(row['longitude']):
            try:
                lon = float(row['longitude'])
                if lon < -180 or lon > 180:
                    validation_results['invalid_coordinates'] += 1
                    has_error = True
                    validation_results['error_details'].append(f"Record {record_num}: Invalid longitude {lon} (must be between -180 and 180)")
            except ValueError:
                validation_results['invalid_coordinates'] += 1
                has_error = True
                validation_results['error_details'].append(f"Record {record_num}: Invalid longitude value '{row['longitude']}'")
        elif 'longitude' in df.columns:
            validation_results['missing_coordinates'] += 1
            has_warning = True
            validation_results['warning_details'].append(f"Record {record_num}: Missing longitude")

        # Validate date
        if 'date' in df.columns and not pd.isna(row['date']):
            date_str = str(row['date']).strip()
            try:
                # Try to parse as YYYY-MM-DD
                datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                validation_results['invalid_dates'] += 1
                has_error = True
                validation_results['error_details'].append(f"Record {record_num}: Invalid date format '{date_str}' (expected YYYY-MM-DD)")
        elif 'date' in df.columns:
            validation_results['invalid_dates'] += 1  # Treat missing as invalid for date? Actually missing required field already caught above.
            # But we'll count it as invalid date for the report.
            has_error = True
            validation_results['error_details'].append(f"Record {record_num}: Missing date")

        # Check recommended fields for warnings
        for field in recommended_fields:
            if field in df.columns:
                if pd.isna(row[field]) or (isinstance(row[field], str) and row[field].strip() == ''):
                    validation_results['missing_recommended_fields'][field] = validation_results['missing_recommended_fields'].get(field, 0) + 1
                    has_warning = True
                    validation_results['warning_details'].append(f"Record {record_num}: Missing recommended field '{field}'")
            else:
                # Column missing entirely
                validation_results['missing_recommended_fields'][field] = validation_results['missing_recommended_fields'].get(field, 0) + 1
                # We'll count this as a warning but only once per column? Let's do per record for simplicity.
                has_warning = True
                validation_results['warning_details'].append(f"Record {record_num}: Missing recommended field '{field}' (column not present)")

        # Update counters
        if has_error:
            validation_results['records_with_errors'] += 1
        if has_warning:
            validation_results['records_with_warnings'] += 1
        if not has_error and not has_warning:
            validation_results['valid_records'] += 1

    # After processing all records, set duplicate count
    validation_results['duplicate_ids'] = len(duplicate_ids)

    # Convert missing field counts to more readable format
    validation_results['missing_required_fields'] = [
        {'field': field, 'missing_count': count}
        for field, count in validation_results['missing_required_fields'].items()
    ]
    validation_results['missing_recommended_fields'] = [
        {'field': field, 'missing_count': count}
        for field, count in validation_results['missing_recommended_fields'].items()
    ]

    return validation_results

def print_validation_report(results, input_file_path):
    """Print a formatted validation report to console and save to file."""
    report_lines = []
    report_lines.append("=" * 60)
    report_lines.append("LANDSLIDE DATA VALIDATION REPORT")
    report_lines.append("=" * 60)
    report_lines.append(f"Input file: {input_file_path}")
    report_lines.append(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")
    report_lines.append("SUMMARY STATISTICS:")
    report_lines.append(f"  Total records processed: {results['total_records']}")
    report_lines.append(f"  Valid records (no errors/warnings): {results['valid_records']}")
    report_lines.append(f"  Records with errors: {results['records_with_errors']}")
    report_lines.append(f"  Records with warnings: {results['records_with_warnings']}")
    report_lines.append("")
    report_lines.append("DATA QUALITY ISSUES:")
    report_lines.append(f"  Duplicate landslide IDs: {results['duplicate_ids']}")
    report_lines.append(f"  Missing coordinates (latitude or longitude): {results['missing_coordinates']}")
    report_lines.append(f"  Invalid coordinates: {results['invalid_coordinates']}")
    report_lines.append(f"  Invalid dates: {results['invalid_dates']}")
    report_lines.append("")

    if results['missing_required_fields']:
        report_lines.append("MISSING REQUIRED FIELDS:")
        for item in results['missing_required_fields']:
            report_lines.append(f"  {item['field']}: {item['missing_count']} missing")
        report_lines.append("")

    if results['missing_recommended_fields']:
        report_lines.append("MISSING RECOMMENDED FIELDS:")
        for item in results['missing_recommended_fields']:
            report_lines.append(f"  {item['field']}: {item['missing_count']} missing")
        report_lines.append("")

    if results['error_details']:
        report_lines.append("ERROR DETAILS (first 10):")
        for error in results['error_details'][:10]:
            report_lines.append(f"  {error}")
        if len(results['error_details']) > 10:
            report_lines.append(f"  ... and {len(results['error_details']) - 10} more errors")
        report_lines.append("")

    if results['warning_details']:
        report_lines.append("WARNING DETAILS (first 10):")
        for warning in results['warning_details'][:10]:
            report_lines.append(f"  {warning}")
        if len(results['warning_details']) > 10:
            report_lines.append(f"  ... and {len(results['warning_details']) - 10} more warnings")
        report_lines.append("")

    report_lines.append("=" * 60)
    report_lines.append("NOTE: This validation does not modify the original data.")
    report_lines.append("Please address issues in your source data file.")
    report_lines.append("=" * 60)

    report_text = "\n".join(report_lines)

    # Print to console
    print(report_text)

    # Save to file
    output_dir = Path(__file__).parent.parent / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"validation_report_{Path(input_file_path).stem}.txt"
    with open(output_file, 'w') as f:
        f.write(report_text)
    print(f"\nValidation report saved to: {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Validate historical landslide CSV data.')
    parser.add_argument('--input', '-i', required=True, help='Path to the input CSV file')
    args = parser.parse_args()

    try:
        results = validate_landslide_csv(args.input)
        print_validation_report(results, args.input)
    except Exception as e:
        print(f"Error during validation: {e}")
        return 1

    return 0

if __name__ == "__main__":
    main()