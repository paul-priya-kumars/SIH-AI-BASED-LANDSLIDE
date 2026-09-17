import os
from pathlib import Path

def create_folder_structure():
    """Create the required folder structure for Phase 1."""
    base_dir = Path(__file__).parent.parent
    directories = [
        base_dir / "data" / "raw",
        base_dir / "data" / "sample",
        base_dir / "output"
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Ensured directory exists: {directory}")

def create_sample_data():
    """Create a sample CSV file with clearly marked synthetic records."""
    sample_data = """landslide_id,date,latitude,longitude,location,district,state,country,source,source_url,severity,description
DEMO-LS-001,2020-05-15,27.7172,85.3239,Kathmandu Valley,Kathmandu,Bagmati,Nepal,Demo Source,https://example.com/demo1,Low,A synthetic landslide record for demonstration purposes only.
DEMO-LS-002,2019-07-22,28.3949,84.1240,Pokhara,Kaski,Gandaki,Nepal,Demo Source,https://example.com/demo2,Medium,Another synthetic record. Not real historical data.
DEMO-LS-003,2021-08-10,30.3165,78.0322,Uttarkashi,Uttarkashi,Uttarakhand,India,Demo Source,https://example.com/demo3,High,Third synthetic record. Do not use for training.
DEMO-LS-004,2018-09-01,22.5726,88.3639,Kolkata,Kolkata,West Bengal,India,Demo Source,https://example.com/demo4,,A record with missing severity.
DEMO-LS-005,2022-06-30,,-80.0,Somewhere,Some District,Some State,USA,Demo Source,https://example.com/demo5,Low,Record with missing latitude.
"""

    sample_file = Path(__file__).parent.parent / "data" / "sample" / "sample_landslides.csv"
    # Only create if file doesn't exist to avoid overwriting
    if not sample_file.exists():
        with open(sample_file, 'w') as f:
            f.write(sample_data)
        print(f"Created sample data file: {sample_file}")
    else:
        print(f"Sample data file already exists: {sample_file}")

def main():
    print("Creating Phase 1 folder structure and sample data...")
    create_folder_structure()
    create_sample_data()
    print("Setup complete!")

if __name__ == "__main__":
    main()