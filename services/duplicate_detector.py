"""
Duplicate detection service
"""

import logging
from typing import List, Dict, Set
from collections import defaultdict
import re

logger = logging.getLogger(__name__)

class DuplicateDetector:
    def __init__(self):
        self.mobile_pattern = re.compile(r'^04\d{8}$')  # Australian mobile pattern
    
    def detect_duplicates(self, records: List[Dict]) -> int:
        """Detect duplicates based on mobile numbers"""
        try:
            logger.info(f"Detecting duplicates in {len(records)} records")
            
            # Group records by mobile number
            mobile_groups = defaultdict(list)
            duplicate_count = 0
            
            for record in records:
                mobile = record.get('mobile', '')
                if mobile and self._is_valid_mobile(mobile):
                    mobile_groups[mobile].append(record)
            
            # Mark duplicates
            for mobile, group_records in mobile_groups.items():
                if len(group_records) > 1:
                    # Mark all but the first as duplicates
                    for i, record in enumerate(group_records):
                        if i > 0:  # Keep the first record, mark others as duplicates
                            record['is_duplicate'] = True
                            duplicate_count += 1
                        else:
                            record['is_duplicate'] = False
            
            logger.info(f"Found {duplicate_count} duplicate records")
            return duplicate_count
            
        except Exception as e:
            logger.error(f"Error detecting duplicates: {e}")
            return 0
    
    def _is_valid_mobile(self, mobile: str) -> bool:
        """Check if mobile number is valid"""
        if not mobile:
            return False
        
        # Clean the mobile number
        cleaned = re.sub(r'\D', '', mobile)
        
        # Check if it matches the pattern
        return bool(self.mobile_pattern.match(cleaned))
    
    def get_duplicate_groups(self, records: List[Dict]) -> List[Dict]:
        """Get duplicate groups with details"""
        try:
            mobile_groups = defaultdict(list)
            
            for record in records:
                mobile = record.get('mobile', '')
                if mobile and self._is_valid_mobile(mobile):
                    mobile_groups[mobile].append(record)
            
            # Return only groups with duplicates
            duplicate_groups = []
            for mobile, group_records in mobile_groups.items():
                if len(group_records) > 1:
                    duplicate_groups.append({
                        'mobile_number': mobile,
                        'record_count': len(group_records),
                        'records': group_records
                    })
            
            return duplicate_groups
            
        except Exception as e:
            logger.error(f"Error getting duplicate groups: {e}")
            return []
    
    def resolve_duplicates(self, duplicate_group: Dict, keep_record_id: str) -> bool:
        """Resolve duplicates by keeping one record and removing others"""
        try:
            records = duplicate_group.get('records', [])
            if not records:
                return False
            
            # Find the record to keep
            keep_record = None
            for record in records:
                if record.get('id') == keep_record_id:
                    keep_record = record
                    break
            
            if not keep_record:
                return False
            
            # Mark the keep record as not duplicate
            keep_record['is_duplicate'] = False
            
            # Mark all other records as duplicates
            for record in records:
                if record.get('id') != keep_record_id:
                    record['is_duplicate'] = True
            
            return True
            
        except Exception as e:
            logger.error(f"Error resolving duplicates: {e}")
            return False
    
    def get_similar_records(self, record: Dict, all_records: List[Dict], threshold: float = 0.8) -> List[Dict]:
        """Find similar records based on multiple criteria"""
        try:
            similar_records = []
            
            for other_record in all_records:
                if other_record.get('id') == record.get('id'):
                    continue
                
                similarity_score = self._calculate_similarity(record, other_record)
                if similarity_score >= threshold:
                    similar_records.append({
                        'record': other_record,
                        'similarity_score': similarity_score
                    })
            
            # Sort by similarity score
            similar_records.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            return similar_records
            
        except Exception as e:
            logger.error(f"Error finding similar records: {e}")
            return []
    
    def _calculate_similarity(self, record1: Dict, record2: Dict) -> float:
        """Calculate similarity score between two records"""
        try:
            score = 0.0
            total_weight = 0.0
            
            # Mobile number comparison (highest weight)
            mobile1 = record1.get('mobile', '')
            mobile2 = record2.get('mobile', '')
            if mobile1 and mobile2:
                if mobile1 == mobile2:
                    score += 1.0 * 0.4  # 40% weight
                total_weight += 0.4
            
            # Name comparison
            name1 = f"{record1.get('first_name', '')} {record1.get('last_name', '')}".strip().lower()
            name2 = f"{record2.get('first_name', '')} {record2.get('last_name', '')}".strip().lower()
            if name1 and name2:
                name_similarity = self._string_similarity(name1, name2)
                score += name_similarity * 0.3  # 30% weight
                total_weight += 0.3
            
            # Address comparison
            address1 = record1.get('address', '').strip().lower()
            address2 = record2.get('address', '').strip().lower()
            if address1 and address2:
                address_similarity = self._string_similarity(address1, address2)
                score += address_similarity * 0.2  # 20% weight
                total_weight += 0.2
            
            # Email comparison
            email1 = record1.get('email', '').strip().lower()
            email2 = record2.get('email', '').strip().lower()
            if email1 and email2:
                if email1 == email2:
                    score += 1.0 * 0.1  # 10% weight
                total_weight += 0.1
            
            # Normalize score
            if total_weight > 0:
                return score / total_weight
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0
    
    def _string_similarity(self, str1: str, str2: str) -> float:
        """Calculate string similarity using Jaccard similarity"""
        try:
            if not str1 or not str2:
                return 0.0
            
            # Convert to sets of words
            words1 = set(str1.split())
            words2 = set(str2.split())
            
            if not words1 and not words2:
                return 1.0
            if not words1 or not words2:
                return 0.0
            
            # Calculate Jaccard similarity
            intersection = len(words1.intersection(words2))
            union = len(words1.union(words2))
            
            return intersection / union if union > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating string similarity: {e}")
            return 0.0
