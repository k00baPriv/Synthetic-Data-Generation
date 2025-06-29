# Test Data Generator

A minimalistic test data generator that uses JSON schemas and OpenAI to generate synthetic data based on user prompts.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file with your OpenAI API key:
```
OPENAI_API_KEY=your_openai_api_key_here
```

## Usage

1. Create a JSON schema file defining your data structure (see `sample_schema.json` for an example)

2. Run the generator:
```bash
python test_data_generator.py your_schema.json
```

3. Enter prompts describing how you want the data to look, for example:
   - "Generate employee data for a tech company with diverse departments"
   - "Create customer records with realistic names and email addresses"
   - "Generate product data for an e-commerce store"

## Example

```bash
python test_data_generator.py sample_schema.json
```

Then enter a prompt like: "Generate 10 employee records for a software company with realistic names and salaries"

## Features

- Loads JSON schema from file
- Interactive prompt-based data generation
- Configurable number of records
- Option to save generated data to file
- Minimal codebase for easy customization 