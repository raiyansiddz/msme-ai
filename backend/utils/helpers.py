"""
Utility functions and helpers for the MSME SaaS platform
"""
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import re
import logging
import calendar

logger = logging.getLogger(__name__)

def generate_uuid() -> str:
    """Generate a unique UUID string"""
    return str(uuid.uuid4())

def generate_invoice_number() -> str:
    """Generate a unique invoice number"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"INV-{timestamp}"

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone: str) -> bool:
    """Validate phone number format"""
    # Remove all non-digit characters
    cleaned_phone = re.sub(r'\D', '', phone)
    # Check if it's a valid length (10-15 digits)
    return 10 <= len(cleaned_phone) <= 15

def format_currency(amount: float, currency: str = "₹") -> str:
    """Format amount as currency"""
    return f"{currency}{amount:,.2f}"

def calculate_tax(amount: float, tax_rate: float = 0.18) -> float:
    """Calculate tax amount"""
    return amount * tax_rate

def calculate_total_with_tax(amount: float, tax_rate: float = 0.18) -> float:
    """Calculate total amount including tax"""
    return amount + calculate_tax(amount, tax_rate)

def sanitize_string(text: str) -> str:
    """Sanitize string input"""
    if not text:
        return ""
    return text.strip()

def convert_to_dict(obj: Any) -> Dict:
    """Convert object to dictionary, handling datetime objects"""
    if hasattr(obj, 'dict'):
        return obj.dict()
    elif isinstance(obj, dict):
        result = {}
        for key, value in obj.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            else:
                result[key] = value
        return result
    else:
        return obj

def paginate_results(results: List, page: int = 1, page_size: int = 10) -> Dict:
    """Paginate results"""
    total_items = len(results)
    total_pages = (total_items + page_size - 1) // page_size
    
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    
    paginated_results = results[start_idx:end_idx]
    
    return {
        "items": paginated_results,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_items": total_items,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }

def get_date_range(period: str) -> tuple:
    """Get date range for reporting periods"""
    today = datetime.now()
    
    if period == "today":
        start_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = today.replace(hour=23, minute=59, second=59, microsecond=999999)
    elif period == "week":
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
    elif period == "month":
        start_date = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        next_month = today.replace(day=28) + timedelta(days=4)
        end_date = next_month - timedelta(days=next_month.day)
    elif period == "quarter":
        quarter = (today.month - 1) // 3 + 1
        start_date = today.replace(month=3 * quarter - 2, day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = today.replace(month=3 * quarter, day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = end_date.replace(day=calendar.monthrange(end_date.year, end_date.month)[1])
    elif period == "year":
        start_date = today.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = today.replace(month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)
    else:
        # Default to last 30 days
        start_date = today - timedelta(days=30)
        end_date = today
    
    return start_date, end_date

def log_api_call(endpoint: str, user_id: str, method: str, status_code: int):
    """Log API call for monitoring"""
    logger.info(f"API Call - {method} {endpoint} - User: {user_id} - Status: {status_code}")

class ResponseHelper:
    """Helper class for API responses"""
    
    @staticmethod
    def success(data: Any = None, message: str = "Success") -> Dict:
        """Create success response"""
        return {
            "success": True,
            "message": message,
            "data": data
        }
    
    @staticmethod
    def error(message: str = "Error", error_code: str = "GENERIC_ERROR") -> Dict:
        """Create error response"""
        return {
            "success": False,
            "message": message,
            "error_code": error_code
        }
    
    @staticmethod
    def paginated_success(data: List, pagination: Dict, message: str = "Success") -> Dict:
        """Create paginated success response"""
        return {
            "success": True,
            "message": message,
            "data": data,
            "pagination": pagination
        }