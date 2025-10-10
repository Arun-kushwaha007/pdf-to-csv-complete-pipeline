import logging
import traceback
import time
from functools import wraps

def retry_on_failure(max_retries=3, delay=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        logging.error(f"Failed after {max_retries} attempts: {str(e)}")
                        raise
                    
                    logging.warning(f"Attempt {attempt + 1} failed: {str(e)}, retrying in {delay}s...")
                    time.sleep(delay)
            
            return None
        return wrapper
    return decorator

def safe_process_pdf(processor, pdf_path, processor_id):
    try:
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        if os.path.getsize(pdf_path) == 0:
            raise ValueError(f"PDF file is empty: {pdf_path}")
        
        @retry_on_failure(max_retries=3, delay=2)
        def process_with_retry():
            return processor.process_document(pdf_path, processor_id)
        
        return process_with_retry()
        
    except Exception as e:
        logging.error(f"Error processing {pdf_path}: {str(e)}")
        logging.error(traceback.format_exc())
        raise
