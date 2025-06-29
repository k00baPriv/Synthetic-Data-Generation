import json
import os
import sys
import csv
import asyncio
from typing import List, Dict, Any, Literal
from dataclasses import dataclass
from dotenv import load_dotenv
from agents import Agent, Runner, trace

# Load environment variables
load_dotenv()

@dataclass
class DataRecord:
    """Represents a single data record with specific fields matching the schema"""
    id: int
    name: str
    email: str
    age: int
    department: str
    salary: float
    is_active: bool
    hire_date: str

@dataclass
class GeneratedRecords:
    """Output type for the data generation agent"""
    records: List[DataRecord]
    count: int

def load_schema(schema_file):
    """Load JSON schema from file"""
    try:
        with open(schema_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Schema file '{schema_file}' not found.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in schema file '{schema_file}'.")
        sys.exit(1)

def create_system_message(schema):
    """Create the system message for the agent"""
    # Extract examples, min/max values from schema
    schema_info = []
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
- records: A list of DataRecord objects, where each DataRecord has the following fields:
  * id: integer (unique identifier)
  * name: string (full name)
  * email: string (email address)
  * age: integer (age in years, 18-100)
  * department: string (department name)
  * salary: number (annual salary, 30000-200000)
  * is_active: boolean (whether employee is active)
  * hire_date: string (date in YYYY-MM-DD format)
- count: The number of records generated

Each record should be a dictionary with field names as keys and values that match the schema types and constraints.

Generate only valid records that strictly follow the schema. If the user doesn't specify the number of records, generate 5 records by default."""
    
    return system_message

async def generate_records(agent, prompt ):
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
        # Convert DataRecord objects to dictionaries for compatibility
        records = []
        for record in response.records:
            record_dict = {
                'id': record.id,
                'name': record.name,
                'email': record.email,
                'age': record.age,
                'department': record.department,
                'salary': record.salary,
                'is_active': record.is_active,
                'hire_date': record.hire_date
            }
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
        sys.exit(1)
    
    schema_file = sys.argv[1]
    
    # Use the agent to run the workflow
    schema = load_schema(schema_file)
    
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
        records = await generate_records(agent, prompt)
        
        if records:
            print("\nGenerated Records:")
            print(json.dumps(records, indent=2))
            
            # Save to file
            save = input("\nSave to file? (y/n): ")
            if save.lower() == 'y':
                filename = input("Filename (default: generated_data.csv): ")
                filename = filename if filename else "generated_data.csv"
                
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