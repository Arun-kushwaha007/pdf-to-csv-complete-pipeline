#!/usr/bin/env python3
"""
Debug script to understand why certain names are failing
"""

import re

def debug_name_parsing(name):
    """Debug the name parsing logic step by step"""
    print(f"\nDebugging: '{name}'")
    
    if not name or not name.strip():
        print("  FAIL: Empty name")
        return "", ""
    
    # Clean the name first
    name = name.strip()
    print(f"  Cleaned name: '{name}'")
    
    # Check if this looks like an address mixed with name (contains numbers)
    if re.search(r'\d', name):
        print("  FAIL: Contains numbers")
        return "", ""
    
    # Check for common address words that shouldn't be in names (whole words only)
    address_words = ['street', 'avenue', 'road', 'drive', 'lane', 'court', 'place', 'way', 
                    'crescent', 'close', 'terrace', 'parade', 'boulevard', 'gordonvale', 
                    'qld', 'nsw', 'vic', 'wa', 'sa', 'tas', 'nt', 'act', 'munno', 'para']
    
    # Check for whole words only, not substrings
    name_lower = name.lower()
    for word in address_words:
        if f' {word} ' in f' {name_lower} ' or name_lower.startswith(f'{word} ') or name_lower.endswith(f' {word}'):
            print(f"  FAIL: Contains address word '{word}'")
            return "", ""
    
    # Split name into parts - use first part as first name, rest as last name
    name_parts = name.split()
    print(f"  Name parts: {name_parts}")
    
    # Must have at least 2 parts for first and last name
    if len(name_parts) < 2:
        print("  FAIL: Less than 2 parts")
        return "", ""
    
    first_name = name_parts[0].strip()
    last_name = " ".join(name_parts[1:]).strip()  # Join all remaining parts as last name
    print(f"  First name: '{first_name}', Last name: '{last_name}'")
    
    # Additional validation - ensure names don't contain numbers
    if re.search(r'\d', first_name) or re.search(r'\d', last_name):
        print("  FAIL: Names contain numbers")
        return "", ""
    
    # Check if first name is too short (less than 2 characters)
    if len(first_name) < 2:
        print("  FAIL: First name too short")
        return "", ""
    
    print("  PASS: Valid name")
    return first_name, last_name

# Test the problematic names
test_names = [
    "Cristian Martinez",
    "CRISTIAN EDGARDO",
    "John Smith",
    "John Michael Smith",
    "Mary Jane"
]

for name in test_names:
    first, last = debug_name_parsing(name)
    print(f"Result: '{name}' -> First: '{first}', Last: '{last}'")
