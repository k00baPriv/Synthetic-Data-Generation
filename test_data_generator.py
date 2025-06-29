import json
import os
import sys
import csv
import asyncio
from typing import List, Dict, Any, Literal
from dataclasses import dataclass
from dotenv import load_dotenv
from agents import Agent, Runner, trace
from pydantic import BaseModel, create_model, ValidationError

# Load environment variables
load_dotenv()

def get_generated_records_model(schema):
    """Dynamically create a GeneratedRecords model based on the schema"""
    # Map JSON schema types to Python types
    type_mapping = {
        'string': str,
        'integer': int,
        'number': float,
        'boolean': bool,
        'array': List,
        'object': Dict
    }
    
    # Create fields for the record model based on schema properties
    record_fields = {}
    for field_name, field_schema in schema.get('properties', {}).items():
        field_type = field_schema.get('type', 'string')
        python_type = type_mapping.get(field_type, str)
        record_fields[field_name] = (python_type, ...)  # ... means required
    
    # Create the record model
    RecordModel = create_model('RecordModel', **record_fields)
    
    # Create the GeneratedRecords model
    generated_records_fields = {
        'records': (List[RecordModel], ...),
        'count': (int, ...)
    }
    
    return create_model('GeneratedRecords', **generated_records_fields)

def load_schema(schema_file):
    """Load JSON schema from file"""
    # If no path separator is provided, assume it's in the schemas folder
    if '/' not in schema_file and '\\' not in schema_file:
        schema_file = os.path.join('schemas', schema_file)
    
    try:
        with open(schema_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Schema file '{schema_file}' not found.")
        print("Make sure the schema file exists in the schemas/ folder or provide the full path.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in schema file '{schema_file}'.")
        sys.exit(1)

def create_system_message(schema):
    """Create the system message for the agent"""
    # Extract examples, min/max values from schema
    schema_info = []
    field_descriptions = []
    
    for field_name, field_schema in schema.get('properties', {}).items():
        field_info = f"- {field_name} ({field_schema.get('type', 'unknown')}): {field_schema.get('description', 'No description')}"
        
        # Add example if available
        if 'example' in field_schema:
            field_info += f" | Example: {field_schema['example']}"
        
        # Add min/max constraints if available
        constraints = []
        if 'minimum' in field_schema:
            constraints.append(f"min: {field_schema['minimum']}")
        if 'maximum' in field_schema:
            constraints.append(f"max: {field_schema['maximum']}")
        
        if constraints:
            field_info += f" | Constraints: {', '.join(constraints)}"
        
        schema_info.append(field_info)
        
        # Build dynamic field description for record model
        field_type = field_schema.get('type', 'unknown')
        field_desc = field_schema.get('description', 'No description')
        
        # Map JSON schema types to Python types
        type_mapping = {
            'string': 'string',
            'integer': 'integer',
            'number': 'number',
            'boolean': 'boolean',
            'array': 'list',
            'object': 'dictionary'
        }
        
        python_type = type_mapping.get(field_type, field_type)
        
        # Add constraints to description
        constraint_info = []
        if 'minimum' in field_schema:
            constraint_info.append(f"min: {field_schema['minimum']}")
        if 'maximum' in field_schema:
            constraint_info.append(f"max: {field_schema['maximum']}")
        if 'format' in field_schema:
            constraint_info.append(f"format: {field_schema['format']}")
        if 'pattern' in field_schema:
            constraint_info.append(f"pattern: {field_schema['pattern']}")
        
        constraint_text = f" ({', '.join(constraint_info)})" if constraint_info else ""
        
        field_descriptions.append(f"  * {field_name}: {python_type} ({field_desc}){constraint_text}")
    
    # Create system message with schema context
    system_message = f"""You are a test data generator. Generate records based on the provided schema and user requirements.

Schema:
{json.dumps(schema, indent=2)}

Schema Details:
{chr(10).join(schema_info)}

IMPORTANT GUIDELINES:
1. Use the example values provided in the schema as a reference for realistic data generation
2. Respect minimum and maximum constraints for numeric fields
3. Follow the data types and formats specified in the schema
4. Generate diverse but realistic data that matches the examples and constraints
5. For fields with examples, use similar patterns but vary the actual values

CRITICAL: You must return a GeneratedRecords object with:
- records: A list of record objects, where each record has the following fields:
{chr(10).join(field_descriptions)}
- count: The number of records generated

Each record should be a dictionary with field names as keys and values that match the schema types and constraints.

Generate only valid records that strictly follow the schema. If the user doesn't specify the number of records, generate 5 records by default."""
    
    return system_message

async def generate_records(agent, prompt, schema):
    """Generate test records using the agent"""
    
    # Use the agent to generate data
    with trace("Data Generation"):
        response = await Runner.run(
            agent,
            f"Generate records based on this prompt: {prompt}"
        )
    
    # The response is now a GeneratedRecords object
    print(f"Response type: {type(response)}")
    print(f"Response attributes: {dir(response) if hasattr(response, '__dict__') else 'No attributes'}")
    
    # Handle RunResult objects
    if hasattr(response, 'final_output'):
        response = response.final_output
        print(f"Final output type: {type(response)}")
    
    if hasattr(response, 'records') and response.records:
        # Convert record objects to dictionaries for compatibility
        records = []
        for record in response.records:
            # Dynamically create record_dict based on schema properties
            record_dict = {}
            for field_name in schema.get('properties', {}).keys():
                if hasattr(record, field_name):
                    record_dict[field_name] = getattr(record, field_name)
            records.append(record_dict)
        return records
    else:
        # Fallback: try to parse as raw JSON if the structured format failed
        print("Structured response failed, trying to parse as raw JSON...")
        if isinstance(response, str):
            content = response.strip()
            # Try to extract JSON from the response
            if content.startswith('```json'):
                content = content[7:-3]  # Remove markdown code blocks
            elif content.startswith('```'):
                content = content[3:-3]
            
            content = content.strip()
            records = json.loads(content)
            return records
        else:
            print("No records generated in response")
            return None

async def main():
    if len(sys.argv) < 2:
        print("Usage: python test_data_generator.py <schema_file.json>")
        print("Schema files should be placed in the 'schemas/' folder.")
        print("Generated CSV files will be saved to the 'csv_output/' folder.")
        print("Examples:")
        print("  python test_data_generator.py product_schema.json")
        print("  python test_data_generator.py sample_schema.json")
        print("  python test_data_generator.py schemas/product_schema.json")
        sys.exit(1)
    
    schema_file = sys.argv[1]
    
    # Use the agent to run the workflow
    schema = load_schema(schema_file)
    
    # Create the dynamic GeneratedRecords model based on the schema
    GeneratedRecords = get_generated_records_model(schema)
    
    # Create system message for the agent
    system_message = create_system_message(schema)
    
    # Create an agent for tracing
    agent = Agent[GeneratedRecords](
        name="Synthetic Data Generator", 
        instructions=system_message,
        output_type=GeneratedRecords
    )
    
    
    print("Test Data Generator")
    print("=" * 50)
    print(f"Loaded schema from: {schema_file}")
    print()
    
    while True:
        prompt = input("Enter your data generation prompt (or 'quit' to exit): ")
        if prompt.lower() == 'quit':
            break
            
        print(f"\nGenerating records...")
        records = await generate_records(agent, prompt, schema)
        
        if records:
            print("\nGenerated Records:")
            print(json.dumps(records, indent=2))
            
            # Save to file
            save = input("\nSave to file? (y/n): ")
            if save.lower() == 'y':
                filename = input("Filename (default: generated_data.csv): ")
                filename = filename if filename else "generated_data.csv"
                
                # If no path separator is provided, save to csv_output folder
                if '/' not in filename and '\\' not in filename:
                    filename = os.path.join('csv_output', filename)
                
                # Get fieldnames from the first record
                if records and len(records) > 0:
                    fieldnames = list(records[0].keys())
                    
                    with open(filename, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        for record in records:
                            writer.writerow(record)
                    print(f"Saved to {filename}")
                else:
                    print("No records to save.")
        else:
            print("Failed to generate records.")
        
        print("\n" + "=" * 50)

if __name__ == "__main__":
    asyncio.run(main()) 