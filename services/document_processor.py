"""
Document processing service using Google Cloud Document AI
"""

import os
import logging
from typing import List, Dict, Optional
from google.cloud import documentai_v1 as documentai
from google.api_core.client_options import ClientOptions
from utils.config import get_settings
import tempfile
import json

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self, settings):
        self.settings = settings
        self.project_id = settings.PROJECT_ID
        self.location = settings.LOCATION
        self.processor_id = settings.CUSTOM_PROCESSOR_ID
        
        # Initialize Document AI client
        if self.location == 'us':
            opts = ClientOptions(api_endpoint="documentai.googleapis.com")
        else:
            opts = ClientOptions(api_endpoint=f"{self.location}-documentai.googleapis.com")
        
        self.client = documentai.DocumentProcessorServiceClient(client_options=opts)
    
    async def process_file(self, file_path: str, job_id: str) -> List[Dict]:
        """Process a single PDF file and extract records"""
        try:
            logger.info(f"Processing file: {file_path}")
            
            # Call Document AI
            document = self._call_document_ai(file_path)
            
            # Extract entities
            entities = self._extract_entities(document)
            
            if not entities:
                logger.warning(f"No entities found in {file_path}")
                return []
            
            # Group entities into records
            records = self._group_entities_to_records(entities)
            
            # Clean and validate records
            clean_records = self._clean_and_validate_records(records)
            
            logger.info(f"Extracted {len(clean_records)} records from {file_path}")
            return clean_records
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            raise
    
    def _call_document_ai(self, file_path: str):
        """Call Google Cloud Document AI"""
        try:
            processor_name = self.client.processor_path(
                self.project_id, self.location, self.processor_id
            )
            
            with open(file_path, "rb") as f:
                content = f.read()
            
            request = documentai.ProcessRequest(
                name=processor_name,
                raw_document=documentai.RawDocument(
                    content=content,
                    mime_type="application/pdf"
                )
            )
            
            result = self.client.process_document(request=request)
            return result.document
            
        except Exception as e:
            logger.error(f"Document AI processing failed: {e}")
            raise
    
    def _extract_entities(self, document) -> List[Dict]:
        """Extract entities from Document AI response"""
        entities = []
        
        for entity in document.entities:
            cleaned_value = self._clean_text(entity.mention_text)
            if cleaned_value:
                entities.append({
                    'type': entity.type_.lower().strip(),
                    'value': cleaned_value,
                    'confidence': entity.confidence
                })
        
        return entities
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        import unicodedata
        import re
        
        # Normalize unicode
        text = unicodedata.normalize('NFKD', text)
        text = ''.join(c for c in text if not unicodedata.combining(c))
        
        # Remove emojis and special characters
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "\U00002702-\U000027B0"  # dingbats
            "\U000024C2-\U0001F251"  # enclosed characters
            "]+", flags=re.UNICODE)
        
        text = emoji_pattern.sub('', text)
        
        # Remove other special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\-.,@()/]', '', text)
        
        # Clean up extra whitespace
        text = ' '.join(text.split())
        
        return text.strip()
    
    def _group_entities_to_records(self, entities: List[Dict]) -> List[Dict]:
        """Group entities into records"""
        records = []
        
        # Extract all field types
        names = [e['value'] for e in entities if e['type'] == 'name']
        mobiles = [e['value'] for e in entities if e['type'] == 'mobile']
        addresses = [e['value'] for e in entities if e['type'] == 'address']
        emails = [e['value'] for e in entities if e['type'] == 'email']
        landlines = [e['value'] for e in entities if e['type'] == 'landline']
        dobs = [e['value'] for e in entities if e['type'] == 'dateofbirth']
        last_seen = [e['value'] for e in entities if e['type'] == 'lastseen']
        
        logger.info(f"Found: {len(names)} names, {len(mobiles)} mobiles, {len(addresses)} addresses, {len(emails)} emails")
        
        # Use the maximum count to ensure we capture all records
        field_counts = [len(names), len(mobiles), len(addresses), len(emails), len(landlines), len(dobs), len(last_seen)]
        max_count = max(field_counts) if any(field_counts) else 0
        
        for i in range(max_count):
            record = {}
            
            if i < len(names):
                record['name'] = names[i]
            if i < len(mobiles):
                record['mobile'] = mobiles[i]
            if i < len(addresses):
                record['address'] = addresses[i]
            if i < len(emails):
                record['email'] = emails[i]
            if i < len(landlines):
                record['landline'] = landlines[i]
            if i < len(dobs):
                record['date_of_birth'] = dobs[i]
            if i < len(last_seen):
                record['last_seen_date'] = last_seen[i]
            
            # Only add records that have at least a name
            if record.get('name'):
                records.append(record)
        
        return records
    
    def _clean_and_validate_records(self, records: List[Dict]) -> List[Dict]:
        """Clean and validate records"""
        clean_records = []
        
        for record in records:
            # Extract and clean all fields
            name = record.get('name', '').strip()
            mobile = record.get('mobile', '').strip()
            address = record.get('address', '').strip()
            email = record.get('email', '').strip()
            landline = record.get('landline', '').strip()
            dob = record.get('date_of_birth', '').strip()
            last_seen = record.get('last_seen_date', '').strip()
            
            # Skip records without a name
            if not name:
                continue
            
            # Parse name into first and last name
            first_name, last_name = self._parse_name(name)
            
            # Skip if we can't get valid first and last names
            if not first_name or not last_name:
                continue
            
            # Clean phone numbers
            mobile_clean = self._clean_phone_number(mobile)
            landline_clean = self._clean_phone_number(landline)
            
            # Mobile number is required (exactly 10 digits)
            if not mobile_clean:
                continue
            
            # Basic email validation
            email_clean = ""
            if email and "@" in email and "." in email.split("@")[-1]:
                email_clean = email.lower().strip()
            
            # Address validation - check first 10 characters for numbers
            address_clean = address
            if address:
                address = address.strip()
                # Remove addresses that are too short
                if len(address) < 15:
                    address_clean = ""
                # Check if first 10 characters contain at least one number
                elif not re.search(r'\d', address[:10]):
                    address_clean = ""
            
            # Address is required
            if not address_clean:
                continue
            
            # Create clean record
            clean_record = {
                'first_name': first_name,
                'last_name': last_name,
                'mobile': mobile_clean,
                'landline': landline_clean,
                'address': address_clean,
                'email': email_clean,
                'date_of_birth': dob,
                'last_seen_date': last_seen,
                'confidence_score': 0.8  # Default confidence
            }
            
            clean_records.append(clean_record)
        
        return clean_records
    
    def _parse_name(self, full_name: str) -> tuple:
        """Parse full name into first and last name"""
        import re
        
        if not full_name or not full_name.strip():
            return "", ""

        name = full_name.strip()

        # If there are separators, choose the best segment
        parts = re.split(r'[;,/\\]\s*', name)
        if len(parts) > 1:
            def latin_score(s: str) -> int:
                return len(re.findall(r'[A-Za-z]', s))

            best = max(parts, key=lambda s: (latin_score(s), len(s)))
            if latin_score(best) >= 1 or len(best.split()) >= 2:
                name = best.strip()

        # Split into tokens and drop leading junk tokens
        tokens = name.split()
        def is_junk_token(tok: str) -> bool:
            stripped = tok.strip(" ,.;:-_()[]{}\"'`")
            if stripped == "":
                return True
            if not re.search(r'[A-Za-z0-9]', stripped):
                return True
            return False

        while tokens and is_junk_token(tokens[0]):
            tokens.pop(0)

        name = " ".join(tokens).strip()
        if not name:
            return "", ""

        # If it contains numbers, likely not a name
        if re.search(r'\d', name):
            return "", ""

        # Address-word blacklist
        address_words = ['street', 'avenue', 'road', 'drive', 'lane', 'court', 'place', 'way',
                        'crescent', 'close', 'terrace', 'parade', 'boulevard', 'qld', 'nsw', 'vic', 'wa', 'sa', 'tas', 'nt', 'act']

        name_lower = name.lower()
        for word in address_words:
            if f' {word} ' in f' {name_lower} ' or name_lower.startswith(f'{word} ') or name_lower.endswith(f' {word}'):
                return "", ""

        name_parts = name.split()
        if len(name_parts) < 2:
            return "", ""

        first_name = name_parts[0].strip()
        last_name = " ".join(name_parts[1:]).strip()

        # Reject names containing digits
        if re.search(r'\d', first_name) or re.search(r'\d', last_name):
            return "", ""

        # Ensure first name has at least 2 letters and contains a Latin letter
        if len(re.sub(r'[^A-Za-z]', '', first_name)) < 2:
            return "", ""

        return first_name, last_name
    
    def _clean_phone_number(self, phone: str) -> str:
        """Clean and validate phone number"""
        import re
        
        if not phone:
            return ""
        
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone)
        
        # Only accept exactly 10 digits
        if len(digits) == 10:
            return digits
        
        # Return empty string for invalid phone numbers
        return ""
