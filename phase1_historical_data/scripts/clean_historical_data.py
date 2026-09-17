import pandas as pd
import argparse
from pathlib import Path
from datetime import datetime
import numpy as np

def clean_landslide_data(input_path, output_path=None):
    """
    Clean historical landslide data.

    Args:
        input_path (str or Path): Path to the input CSV file.
        output_path (str or Path, optional): Path to save the cleaned CSV.
            If not provided, saves to phase1_historical_data/data/cleaned/ with prefix 'cleaned_'.

    Returns:
        dict: Cleaning results and statistics.
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

    # Make a copy for cleaning to preserve original
    df_clean = df.copy()

    # Initialize statistics
    stats = {
        'total_records': len(df),
        'records_cleaned': 0,
        'records_require_review': 0,
        'exact_duplicate_rows': 0,
        'duplicate_landslide_ids': 0,
        'possible_spatial_duplicates': 0,
        'missing_required_values': 0,
        'invalid_coordinates': 0,
        'invalid_dates': 0,
        'dates_standardized': 0,
        'coordinates_converted': 0,
        'text_fields_normalized': 0,
        'review_reasons': []
    }

    # We'll track indices for review
    review_indices = set()

    # Helper function to check if a value is missing (NaN or empty string)
    def is_missing(val):
        return pd.isna(val) or (isinstance(val, str) and val.strip() == '')

    # 1. Clean text fields (location, district, state, country, source, source_url, severity, description)
    text_fields = ['location', 'district', 'state', 'country', 'source', 'source_url', 'severity', 'description']
    for field in text_fields:
        if field in df_clean.columns:
            # Store original for comparison
            original = df_clean[field].copy()
            # Clean: strip whitespace, replace multiple spaces with single space
            df_clean[field] = df_clean[field].apply(
                lambda x: ' '.join(str(x).strip().split()) if not is_missing(x) else x
            )
            # Count how many were changed (excluding missing values)
            changed = ((original != df_clean[field]) & (~original.isna()) & (original != '')).sum()
            stats['text_fields_normalized'] += changed

    # 2. Clean landslide_id: strip whitespace
    if 'landslide_id' in df_clean.columns:
        original = df_clean['landslide_id'].copy()
        df_clean['landslide_id'] = df_clean['landslide_id'].apply(
            lambda x: str(x).strip() if not is_missing(x) else x
        )
        # Count changes
        changed = ((original != df_clean['landslide_id']) & (~original.isna()) & (original != '')).sum()
        stats['text_fields_normalized'] += changed  # count as text normalization

    # 3. Standardize dates
    if 'date' in df_clean.columns:
        original_dates = df_clean['date'].copy()
        standardized_dates = []
        for val in original_dates:
            if is_missing(val):
                standardized_dates.append(val)
                continue
            val_str = str(val).strip()
            # Try to parse common formats
            parsed = None
            # Try YYYY-MM-DD
            try:
                parsed = datetime.strptime(val_str, '%Y-%m-%d')
            except ValueError:
                pass
            # Try YYYY/MM/DD
            if parsed is None:
                try:
                    parsed = datetime.strptime(val_str, '%Y/%m/%d')
                except ValueError:
                    pass
            # Try DD-MM-YYYY
            if parsed is None:
                try:
                    parsed = datetime.strptime(val_str, '%d-%m-%Y')
                except ValueError:
                    pass
            # Try MM/DD/YYYY
            if parsed is None:
                try:
                    parsed = datetime.strptime(val_str, '%m/%d/%Y')
                except ValueError:
                    pass
            # Try DD/MM/YYYY
            if parsed is None:
                try:
                    parsed = datetime.strptime(val_str, '%d/%m/%Y')
                except ValueError:
                    pass
            # If parsed, standardize to YYYY-MM-DD
            if parsed is not None:
                standardized_dates.append(parsed.strftime('%Y-%m-%d'))
                stats['dates_standardized'] += 1
            else:
                # Could not parse, keep original and flag for review
                standardized_dates.append(val)
                review_indices.add(len(standardized_dates)-1)  # index of this record
                stats['invalid_dates'] += 1
        df_clean['date'] = standardized_dates

    # 4. Clean and validate latitude
    if 'latitude' in df_clean.columns:
        original_lat = df_clean['latitude'].copy()
        cleaned_lat = []
        for i, val in enumerate(original_lat):
            if is_missing(val):
                cleaned_lat.append(val)
                review_indices.add(i)
                stats['missing_required_values'] += 1
                continue
            try:
                lat_float = float(val)
                # Check range
                if -90 <= lat_float <= 90:
                    cleaned_lat.append(lat_float)
                    if isinstance(val, str) and val.strip() != str(lat_float):
                        stats['coordinates_converted'] += 1
                else:
                    # Invalid range
                    cleaned_lat.append(np.nan)  # will be handled as missing later
                    review_indices.add(i)
                    stats['invalid_coordinates'] += 1
            except (ValueError, TypeError):
                # Not a number
                cleaned_lat.append(np.nan)
                review_indices.add(i)
                stats['invalid_coordinates'] += 1
        df_clean['latitude'] = cleaned_lat

    # 5. Clean and validate longitude
    if 'longitude' in df_clean.columns:
        original_lon = df_clean['longitude'].copy()
        cleaned_lon = []
        for i, val in enumerate(original_lon):
            if is_missing(val):
                cleaned_lon.append(val)
                review_indices.add(i)
                stats['missing_required_values'] += 1
                continue
            try:
                lon_float = float(val)
                # Check range
                if -180 <= lon_float <= 180:
                    cleaned_lon.append(lon_float)
                    if isinstance(val, str) and val.strip() != str(lon_float):
                        stats['coordinates_converted'] += 1
                else:
                    # Invalid range
                    cleaned_lon.append(np.nan)
                    review_indices.add(i)
                    stats['invalid_coordinates'] += 1
            except (ValueError, TypeError):
                # Not a number
                cleaned_lon.append(np.nan)
                review_indices.add(i)
                stats['invalid_coordinates'] += 1
        df_clean['longitude'] = cleaned_lon

    # 6. Detect duplicate rows (exact duplicates)
    # We consider all columns for exact duplicate
    duplicate_rows = df_clean.duplicated(keep='first')
    stats['exact_duplicate_rows'] = duplicate_rows.sum()
    # Mark these for review? We'll keep them but note in report.
    # We'll add the indices of duplicates (excluding the first occurrence) to review for duplicate ID check later?
    # Actually, we'll handle duplicate IDs separately.

    # 7. Detect duplicate landslide IDs
    if 'landslide_id' in df_clean.columns:
        # Only consider non-missing IDs for duplicate ID check
        non_missing_ids = df_clean['landslide_id'].dropna()
        # But note: we converted to string, so empty string might be present? We'll treat empty string as missing for ID?
        # Let's consider: if landslide_id is empty string after stripping, we treat as missing.
        id_series = df_clean['landslide_id'].astype(str)
        id_series = id_series.replace('nan', np.nan)  # from NaN conversion
        id_series = id_series.replace('', np.nan)     # empty string to NaN
        # Now check duplicates on non-null
        duplicate_id_mask = id_series.duplicated(keep=False) & id_series.notna()
        stats['duplicate_landslide_ids'] = duplicate_id_mask.sum()
        # Mark records with duplicate IDs for review (all but the first? we'll mark all duplicates)
        duplicate_id_indices = id_series[duplicate_id_mask].index
        review_indices.update(duplicate_id_indices)

    # 8. Detect possible spatial duplicates (same date, latitude, longitude)
    # We'll consider a record as possible spatial duplicate if there's another record with same date, lat, lon (all non-missing)
    # We'll do a simple approach: group by date, latitude, longitude and flag groups with size > 1
    # But note: we must be cautious about missing values in these fields.
    spatial_key = ['date', 'latitude', 'longitude']
    if all(field in df_clean.columns for field in spatial_key):
        # Create a temporary dataframe with only these columns, drop rows where any is missing
        spatial_df = df_clean[spatial_key].dropna()
        if not spatial_df.empty:
            # Group by the three columns and count
            group_counts = spatial_df.groupby(spatial_key).size()
            # Groups with count > 1 are possible spatial duplicates
            possible_duplicate_groups = group_counts[group_counts > 1]
            stats['possible_spatial_duplicates'] = possible_duplicate_groups.sum()
            # We could mark these records for review, but for now just count.
            # We'll add the indices of these records to review?
            # Let's get the indices of the rows that are in these groups.
            # We'll do a merge to get the indices.
            if not possible_duplicate_groups.empty:
                # Reset index to have a column for index
                spatial_df_reset = spatial_df.reset_index()
                # Merge with the group counts to get the count per group
                merged = spatial_df_reset.merge(
                    possible_duplicate_groups.reset_index(name='count'),
                    on=spatial_key
                )
                # These indices are the ones that are in a group with count>1
                possible_duplicate_indices = merged['index'].tolist()
                review_indices.update(possible_duplicate_indices)

    # 9. Determine which records are cleaned vs require review
    # We'll consider a record as requiring review if it's in review_indices
    # But note: we also want to count records that are cleaned (no issues) and those that require review.
    # However, a record might have multiple issues but we count it once for review.
    stats['records_require_review'] = len(review_indices)
    stats['records_cleaned'] = stats['total_records'] - stats['records_require_review']

    # 10. Add a data_quality_status column
    df_clean['data_quality_status'] = 'CLEAN'
    df_clean.loc[list(review_indices), 'data_quality_status'] = 'REVIEW_REQUIRED'

    # 11. Determine output path
    if output_path is None:
        output_dir = input_path.parent.parent / 'cleaned'
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"cleaned_{input_path.name}"
    else:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

    # 12. Save the cleaned data
    df_clean.to_csv(output_path, index=False)

    # 13. Generate a cleaning report (we'll return stats and also print/save a report)
    return stats, output_path

def print_cleaning_report(stats, input_file_path, output_file_path):
    """Print a formatted cleaning report to console."""
    report_lines = []
    report_lines.append("=" * 60)
    report_lines.append("HISTORICAL LANDSLIDE DATA CLEANING REPORT")
    report_lines.append("=" * 60)
    report_lines.append(f"Input file: {input_file_path}")
    report_lines.append(f"Output file: {output_file_path}")
    report_lines.append(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")
    report_lines.append("SUMMARY STATISTICS:")
    report_lines.append(f"  Total records processed: {stats['total_records']}")
    report_lines.append(f"  Records successfully cleaned: {stats['records_cleaned']}")
    report_lines.append(f"  Records requiring review: {stats['records_require_review']}")
    report_lines.append("")
    report_lines.append("DUPLICATES:")
    report_lines.append(f"  Exact duplicate rows: {stats['exact_duplicate_rows']}")
    report_lines.append(f"  Duplicate landslide IDs: {stats['duplicate_landslide_ids']}")
    report_lines.append(f"  Possible spatial duplicates (same date, lat, lon): {stats['possible_spatial_duplicates']}")
    report_lines.append("")
    report_lines.append("DATA QUALITY ISSUES:")
    report_lines.append(f"  Missing required values: {stats['missing_required_values']}")
    report_lines.append(f"  Invalid coordinates: {stats['invalid_coordinates']}")
    report_lines.append(f"  Invalid dates: {stats['invalid_dates']}")
    report_lines.append("")
    report_lines.append("CLEANING ACTIONS PERFORMED:")
    report_lines.append(f"  Dates standardized: {stats['dates_standardized']}")
    report_lines.append(f"  Coordinates converted (to numeric): {stats['coordinates_converted']}")
    report_lines.append(f"  Text fields normalized (whitespace): {stats['text_fields_normalized']}")
    report_lines.append("")
    report_lines.append("=" * 60)
    report_lines.append("NOTE: The original raw data remains unchanged.")
    report_lines.append("Review the output file and consider manual review for records marked REVIEW_REQUIRED.")
    report_lines.append("=" * 60)

    report_text = "\n".join(report_lines)
    print(report_text)

    # Also save the report to a file
    report_dir = Path(__file__).parent.parent / 'output'
    report_dir.mkdir(parents=True, exist_ok=True)
    report_file = report_dir / f"cleaning_report_{Path(input_file_path).stem}.txt"
    with open(report_file, 'w') as f:
        f.write(report_text)
    print(f"\nCleaning report saved to: {report_file}")

def main():
    parser = argparse.ArgumentParser(description='Clean historical landslide CSV data.')
    parser.add_argument('--input', '-i', required=True, help='Path to the input CSV file')
    parser.add_argument('--output', '-o', help='Path to save the cleaned CSV (optional)')
    args = parser.parse_args()

    try:
        stats, output_path = clean_landslide_data(args.input, args.output)
        print_cleaning_report(stats, args.input, output_path)
    except Exception as e:
        print(f"Error during cleaning: {e}")
        return 1

    return 0

if __name__ == "__main__":
    main()