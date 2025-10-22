import os
import re
import pandas as pd
from google.cloud import documentai_v1 as documentai
from google.api_core.client_options import ClientOptions
from typing import List, Dict
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WorkingDocumentProcessor:
    def __init__(self, project_id: str, location: str, processor_id: str, credentials_path: str, db_config: Dict = None):
        self.project_id = project_id
        self.location = location
        self.processor_id = processor_id
        self.credentials_path = credentials_path
        self.db_config = db_config
        
        # Set credentials
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
        
        opts = ClientOptions(api_endpoint=f"{location}-documentai.googleapis.com")
        self.client = documentai.DocumentProcessorServiceClient(client_options=opts)
        
        # Initialize database connection if config provided
        self.db_connection = None
        if db_config:
            self._init_database()
    
    def process_document(self, file_path: str) -> List[Dict]:
        """Process a single document and return both raw and filtered records"""
        logger.info(f"Processing document: {file_path}")

        document = self._call_custom_extractor(file_path, self.processor_id)

        entities = self._extract_entities_simple(document)
        logger.info(f"📊 Found {len(entities)} entities")
        
        if len(entities) == 0:
            logger.error("❌ NO ENTITIES FOUND - Check processor ID and document format")
            return []
        
        # Get raw records (no filtering)
        raw_records = self._simple_grouping(entities)
        logger.info(f"Raw records: {len(raw_records)}")
        
        # Get filtered records (with validation)
        filtered_records = self._clean_and_validate(raw_records)
        logger.info(f"Filtered records: {len(filtered_records)}")
        
        # Return both raw and filtered
        return {
            'raw_records': raw_records,
            'filtered_records': filtered_records,
            'file_name': os.path.basename(file_path)
        }
    
    def _call_custom_extractor(self, file_path: str, processor_id: str):
        processor_name = self.client.processor_path(
            self.project_id, self.location, processor_id
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
    
    def _extract_entities_simple(self, document):
        entities = []
        
        for entity in document.entities:
            entity_type = entity.type_.lower().strip()
            entity_value = entity.mention_text.strip()
            
            # Debug logging
            logger.info(f"Entity found: type='{entity_type}', value='{entity_value}'")
            
            entities.append({
                'type': entity_type,
                'value': entity_value
            })
        
        logger.info(f"Total entities extracted: {len(entities)}")
        return entities
    
    def _simple_grouping(self, entities: List[Dict]) -> List[Dict]:
        """Group entities into records without filtering"""
        records = []
        names = [e['value'] for e in entities if 'name' in e['type']]
        mobiles = [e['value'] for e in entities if 'mobile' in e['type'] or 'phone' in e['type']]
        addresses = [e['value'] for e in entities if 'address' in e['type']]
        emails = [e['value'] for e in entities if 'email' in e['type']]
        
        logger.info(f"Found: {len(names)} names, {len(mobiles)} mobiles, {len(addresses)} addresses, {len(emails)} emails")
        
        # Debug: Show what entity types we found
        entity_types = [e['type'] for e in entities]
        logger.info(f"Entity types found: {set(entity_types)}")
        
        max_count = max(len(names), len(mobiles), len(addresses), len(emails)) if any([names, mobiles, addresses, emails]) else 0
        
        for i in range(max_count):
            record = {}
            
            if i < len(names):
                # Split name into first and last
                name_parts = names[i].split()
                if len(name_parts) >= 2:
                    record['first_name'] = name_parts[0]
                    record['last_name'] = ' '.join(name_parts[1:])
                else:
                    record['first_name'] = names[i]
                    record['last_name'] = ''
            if i < len(mobiles):
                record['mobile'] = mobiles[i]
            if i < len(addresses):
                record['address'] = addresses[i]
            if i < len(emails):
                record['email'] = emails[i]
            
            if record.get('first_name'):
                records.append(record)
                logger.info(f"Created record {i+1}: {record}")
        
        logger.info(f"Created {len(records)} records total")
        return records
    
    def _fix_address_ordering(self, address: str) -> str:
        """Fix address ordering where postcode/state appears before street address"""
        if not address:
            return address
            
        address = address.strip()
        
        # Pattern 1: Postcode and state at the beginning
        # Matches: NSW 2289 114 Northcott Drive ADAMSTOWN HEIGHTS
        postcode_state_pattern = r'^([A-Z]{2,3}\s+\d{4})\s+(.+)$'
        match = re.match(postcode_state_pattern, address)
        
        if match:
            postcode_state = match.group(1)  # NSW 2289
            street_address = match.group(2)  # 114 Northcott Drive ADAMSTOWN HEIGHTS
            # Reorder: street_address + postcode_state
            return f"{street_address} {postcode_state}"
        
        # Pattern 2: Postcode at the beginning without state
        # Matches: 2289 114 Northcott Drive ADAMSTOWN HEIGHTS NSW
        postcode_only_pattern = r'^(\d{4})\s+(.+?)\s+([A-Z]{2,3})$'
        match = re.match(postcode_only_pattern, address)
        
        if match:
            postcode = match.group(1)  # 2289
            street_address = match.group(2)  # 114 Northcott Drive ADAMSTOWN HEIGHTS
            state = match.group(3)  # NSW
            # Reorder: street_address + state + postcode
            return f"{street_address} {state} {postcode}"
        
        # Pattern 3: State and postcode in the middle
        # Matches: 114 Northcott Drive NSW 2289 ADAMSTOWN HEIGHTS
        state_postcode_middle_pattern = r'^(.+?)\s+([A-Z]{2,3}\s+\d{4})\s+(.+)$'
        match = re.match(state_postcode_middle_pattern, address)
        
        if match:
            street_part1 = match.group(1)  # 114 Northcott Drive
            state_postcode = match.group(2)  # NSW 2289
            street_part2 = match.group(3)  # ADAMSTOWN HEIGHTS
            # Reorder: street_part1 + street_part2 + state_postcode
            return f"{street_part1} {street_part2} {state_postcode}"
        
        return address

    def _clean_and_validate(self, records: List[Dict]) -> List[Dict]:
        """Clean validation - mobile required, proper name format, address validation"""
        clean_records = []
        
        for record in records:
            name = record.get('name', '').strip()
            mobile = record.get('mobile', '').strip()  
            address = record.get('address', '').strip()
            email = record.get('email', '').strip()
            
            if not name:
                continue
            
            name_parts = name.split()
            if len(name_parts) < 2:
                continue
                
            first_name = name_parts[0]
            last_name = name_parts[1] 
            
            if len(first_name) <= 1:
                continue

            if not mobile:
                continue
                
            mobile_digits = re.sub(r'\D', '', mobile)
            if not (len(mobile_digits) == 10 and mobile_digits.startswith('04')):
                continue

            if not address or not re.search(r'\d', address[:10]):
                continue
            
            # Fix address ordering
            fixed_address = self._fix_address_ordering(address)
            
            clean_records.append({
                'first_name': first_name,
                'last_name': last_name, 
                'mobile': mobile_digits,
                'address': fixed_address,
                'email': email if email else ''
            })
        
        # Remove duplicates based on mobile
        unique_records = []
        seen_mobiles = set()
        
        for record in clean_records:
            mobile = record['mobile']
            if mobile not in seen_mobiles:
                unique_records.append(record)
                seen_mobiles.add(mobile)
        
        return unique_records
    
    def detect_duplicates(self, records: List[Dict]) -> List[Dict]:
        """Detect duplicate records based on mobile number"""
        if not records:
            return []
        
        mobile_counts = {}
        duplicates = []
        
        for record in records:
            mobile = record.get('mobile', '')
            if mobile in mobile_counts:
                mobile_counts[mobile].append(record)
            else:
                mobile_counts[mobile] = [record]
        
        for mobile, records_list in mobile_counts.items():
            if len(records_list) > 1:
                for record in records_list:
                    record['duplicate_mobile'] = mobile
                    record['duplicate_count'] = len(records_list)
                    duplicates.append(record)
        
        return duplicates
    
    def save_csv(self, records: List[Dict], output_path: str, include_metadata: bool = False):
        """Save records to CSV"""
        if not records:
            logger.warning("No records to save")
            return
        
        df = pd.DataFrame(records)
        
        # Standardize column order
        standard_columns = ['first_name', 'last_name', 'mobile', 'address', 'email']
        if include_metadata:
            standard_columns.extend(['file_name', 'extraction_date'])
        
        # Only include columns that exist in the data
        available_columns = [col for col in standard_columns if col in df.columns]
        df = df[available_columns]
        
        df.to_csv(output_path, index=False)
        logger.info(f"💾 Saved {len(records)} records to {output_path}")

    def save_excel(self, records: List[Dict], output_path: str, include_metadata: bool = False):
        """Save records to Excel"""
        if not records:
            logger.warning("No records to save")
            return
        
        df = pd.DataFrame(records)
        
        # Standardize column order
        standard_columns = ['first_name', 'last_name', 'mobile', 'address', 'email']
        if include_metadata:
            standard_columns.extend(['file_name', 'extraction_date'])
        
        # Only include columns that exist in the data
        available_columns = [col for col in standard_columns if col in df.columns]
        df = df[available_columns]
        
        df.to_excel(output_path, index=False)
        logger.info(f"💾 Saved {len(records)} records to {output_path}")

    def process_multiple_documents(self, file_paths: List[str]) -> Dict:
        """Process multiple documents and return combined results"""
        all_raw_records = []
        all_filtered_records = []
        processed_files = []
        
        for file_path in file_paths:
            try:
                result = self.process_document(file_path)
                if result:
                    all_raw_records.extend(result['raw_records'])
                    all_filtered_records.extend(result['filtered_records'])
                    processed_files.append(result['file_name'])
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
        
        return {
            'raw_records': all_raw_records,
            'filtered_records': all_filtered_records,
            'processed_files': processed_files,
            'total_raw': len(all_raw_records),
            'total_filtered': len(all_filtered_records)
        }

    def _init_database(self):
        """Initialize database connection"""
        try:
            self.db_connection = psycopg2.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                database=self.db_config['database'],
                user=self.db_config['user'],
                password=self.db_config['password']
            )
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            self.db_connection = None

    def _get_db_connection(self):
        """Get database connection, reconnect if needed"""
        if not self.db_connection or self.db_connection.closed:
            self._init_database()
        return self.db_connection

    def save_to_database(self, raw_records: List[Dict], filtered_records: List[Dict], 
                        file_name: str, session_name: str = None) -> bool:
        """Save records to database"""
        if not self.db_connection:
            logger.warning("No database connection available")
            return False
        
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            # Create session if provided
            session_id = None
            if session_name:
                cursor.execute("""
                    INSERT INTO processing_sessions (session_name, total_files, raw_records_count, filtered_records_count)
                    VALUES (%s, %s, %s, %s) RETURNING id
                """, (session_name, 1, len(raw_records), len(filtered_records)))
                session_id = cursor.fetchone()[0]
            
            # Insert raw records
            for record in raw_records:
                # Create full_name from first_name and last_name
                first_name = record.get('first_name', '')
                last_name = record.get('last_name', '')
                full_name = f"{first_name} {last_name}".strip() if first_name or last_name else ''
                
                cursor.execute("""
                    INSERT INTO raw_records (file_name, full_name, first_name, last_name, mobile, 
                                           landline, email, address, date_of_birth, last_seen)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    file_name,
                    full_name,
                    first_name,
                    last_name,
                    record.get('mobile', ''),
                    record.get('landline', ''),
                    record.get('email', ''),
                    record.get('address', ''),
                    record.get('date_of_birth', ''),
                    record.get('last_seen', '')
                ))
            
            # Insert filtered records (with duplicate handling)
            for record in filtered_records:
                cursor.execute("""
                    INSERT INTO filtered_records (file_name, first_name, last_name, mobile, 
                                                landline, email, address)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (mobile) DO UPDATE SET
                        file_name = EXCLUDED.file_name,
                        first_name = EXCLUDED.first_name,
                        last_name = EXCLUDED.last_name,
                        landline = EXCLUDED.landline,
                        email = EXCLUDED.email,
                        address = EXCLUDED.address,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    file_name,
                    record.get('first_name', ''),
                    record.get('last_name', ''),
                    record.get('mobile', ''),
                    record.get('landline', ''),
                    record.get('email', ''),
                    record.get('address', '')
                ))
            
            conn.commit()
            logger.info(f"Saved {len(raw_records)} raw and {len(filtered_records)} filtered records to database")
            return True
            
        except Exception as e:
            logger.error(f"Error saving to database: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if cursor:
                cursor.close()

    def get_records_from_database(self, record_type: str = 'filtered', limit: int = 1000) -> List[Dict]:
        """Get records from database"""
        if not self.db_connection:
            logger.warning("No database connection available")
            return []
        
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            table_name = f"{record_type}_records"
            cursor.execute(f"""
                SELECT * FROM {table_name} 
                ORDER BY created_at DESC 
                LIMIT %s
            """, (limit,))
            
            records = cursor.fetchall()
            return [dict(record) for record in records]
            
        except Exception as e:
            logger.error(f"Error getting records from database: {e}")
            return []
        finally:
            if cursor:
                cursor.close()

    def get_database_stats(self) -> Dict:
        """Get database statistics"""
        if not self.db_connection:
            return {}
        
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            # Get counts
            cursor.execute("SELECT COUNT(*) FROM raw_records")
            raw_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM filtered_records")
            filtered_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT file_name) FROM raw_records")
            file_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT mobile) FROM filtered_records")
            unique_mobiles = cursor.fetchone()[0]
            
            return {
                'raw_records': raw_count,
                'filtered_records': filtered_count,
                'files_processed': file_count,
                'unique_mobiles': unique_mobiles
            }
            
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {}
        finally:
            if cursor:
                cursor.close()

    def close_database(self):
        """Close database connection"""
        if self.db_connection:
            self.db_connection.close()
            self.db_connection = None