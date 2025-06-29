# Schemas Folder

This folder contains JSON schema files that define the structure of test data to be generated.

## Available Schemas

- `product_schema.json` - Schema for product data
- `sample_schema.json` - Sample schema for testing

## Usage

When running the test data generator, you can reference schemas in this folder in two ways:

1. **Just the filename** (recommended):
   ```bash
   python test_data_generator.py product_schema.json
   ```

2. **Full path**:
   ```bash
   python test_data_generator.py schemas/product_schema.json
   ```

## Schema Format

Each schema file should follow JSON Schema format and include:
- `properties`: Object defining the fields and their types
- `required`: Array of required field names
- Field descriptions and examples for better data generation

## Adding New Schemas

To add a new schema:
1. Create a new `.json` file in this folder
2. Follow the JSON Schema format
3. Include field descriptions and examples for better results
4. Use the filename when running the generator 