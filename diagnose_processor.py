#!/usr/bin/env python3
"""
Diagnostic script to check Document AI processor configuration
"""

import os
from google.cloud import documentai_v1 as documentai
from google.api_core.client_options import ClientOptions

def diagnose_processor():
    """Diagnose Document AI processor configuration"""
    
    # Get configuration from environment
    project_id = os.getenv('PROJECT_ID', 'pdf2csv-converter-tool')
    location = os.getenv('LOCATION', 'us')
    processor_id = os.getenv('CUSTOM_PROCESSOR_ID', 'e3a0679d2b58c372')
    
    print("=== Document AI Processor Diagnosis ===")
    print(f"Project ID: {project_id}")
    print(f"Location: {location}")
    print(f"Processor ID: {processor_id}")
    print()
    
    try:
        # Configure client with correct endpoint
        if location == 'us':
            opts = ClientOptions(api_endpoint="documentai.googleapis.com")
        else:
            opts = ClientOptions(api_endpoint=f"{location}-documentai.googleapis.com")
        
        client = documentai.DocumentProcessorServiceClient(client_options=opts)
        
        # Try to get the processor
        processor_name = client.processor_path(project_id, location, processor_id)
        print(f"Processor path: {processor_name}")
        
        # Get processor details
        processor = client.get_processor(name=processor_name)
        print(f"Processor found!")
        print(f"  Name: {processor.display_name}")
        print(f"  Type: {processor.type_}")
        print(f"  State: {processor.state}")
        print(f"  Create time: {processor.create_time}")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        print()
        
        # Try to list all processors in the project
        print("Attempting to list all processors in the project...")
        try:
            if location == 'us':
                opts = ClientOptions(api_endpoint="documentai.googleapis.com")
            else:
                opts = ClientOptions(api_endpoint=f"{location}-documentai.googleapis.com")
            
            client = documentai.DocumentProcessorServiceClient(client_options=opts)
            parent = f"projects/{project_id}/locations/{location}"
            
            response = client.list_processors(parent=parent)
            processors = list(response)
            
            if processors:
                print(f"Found {len(processors)} processors:")
                for i, proc in enumerate(processors):
                    print(f"  {i+1}. {proc.display_name}")
                    print(f"     ID: {proc.name.split('/')[-1]}")
                    print(f"     Type: {proc.type_}")
                    print(f"     State: {proc.state}")
                    print()
            else:
                print("No processors found in this project/location.")
                
        except Exception as list_error:
            print(f"Error listing processors: {list_error}")
        
        return False

def test_alternative_locations():
    """Test different possible locations"""
    project_id = os.getenv('PROJECT_ID', 'pdf2csv-converter-tool')
    processor_id = os.getenv('CUSTOM_PROCESSOR_ID', 'e3a0679d2b58c372')
    
    possible_locations = ['us', 'us-central1', 'us-east1', 'us-west1', 'us-west2', 'us-west3', 'us-west4']
    
    print("\n=== Testing Alternative Locations ===")
    
    for location in possible_locations:
        print(f"\nTesting location: {location}")
        try:
            if location == 'us':
                opts = ClientOptions(api_endpoint="documentai.googleapis.com")
            else:
                opts = ClientOptions(api_endpoint=f"{location}-documentai.googleapis.com")
            
            client = documentai.DocumentProcessorServiceClient(client_options=opts)
            processor_name = client.processor_path(project_id, location, processor_id)
            processor = client.get_processor(name=processor_name)
            
            print(f"  FOUND! Processor: {processor.display_name}")
            print(f"    State: {processor.state}")
            return location
            
        except Exception as e:
            print(f"  Not found: {str(e)[:100]}...")
    
    return None

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv('config.env')
    
    # If using application default credentials, don't set GOOGLE_APPLICATION_CREDENTIALS
    if 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
        # Check if the file exists and is valid
        creds_file = os.environ['GOOGLE_APPLICATION_CREDENTIALS']
        if not os.path.exists(creds_file) or 'to be updated' in creds_file:
            print("Warning: GOOGLE_APPLICATION_CREDENTIALS points to invalid file.")
            print("Using application default credentials instead.")
            if 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
                del os.environ['GOOGLE_APPLICATION_CREDENTIALS']
    
    # Run diagnosis
    success = diagnose_processor()
    
    if not success:
        # Try alternative locations
        correct_location = test_alternative_locations()
        if correct_location:
            print(f"\nSOLUTION FOUND!")
            print(f"Update your config.env file:")
            print(f"LOCATION={correct_location}")
        else:
            print(f"\nProcessor not found in any common locations.")
            print("Please verify:")
            print("1. The processor ID is correct")
            print("2. The processor exists and is enabled")
            print("3. Your service account has proper permissions")
            print("4. The processor is in the correct project")
