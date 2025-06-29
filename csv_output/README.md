# CSV Output Folder

This folder contains CSV files with generated test data from the synthetic data generator.

## Contents

- `generated_data.csv` - Previously generated test data

## Usage

When you run the test data generator and choose to save the results, CSV files will be automatically saved to this folder.

### Default Behavior

- If you don't specify a path when saving, files will be saved here
- Example: `generated_data.csv` → `csv_output/generated_data.csv`

### Custom Paths

You can still specify custom paths when saving:
- `my_data.csv` → `csv_output/my_data.csv`
- `../results.csv` → `../results.csv` (saves outside the folder)
- `data/my_results.csv` → `data/my_results.csv` (saves to custom folder)

## File Format

All CSV files in this folder contain:
- Header row with field names from the schema
- Data rows with generated test data
- UTF-8 encoding for proper character support

## Organization

Consider organizing your output files by:
- Date: `2024-01-15_product_data.csv`
- Schema type: `product_data.csv`, `user_data.csv`
- Generation parameters: `large_dataset.csv`, `small_sample.csv` 