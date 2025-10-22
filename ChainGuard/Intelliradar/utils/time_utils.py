"""
Time utility module for normalizing various date formats to ISO 8601 format.
"""

import re
from datetime import datetime, timedelta
from typing import Optional, Union
import logging

logger = logging.getLogger(__name__)

def normalize_datetime(date_input: Union[str, None], timezone_offset: int = 0) -> Union[str, None]:
    """
    Convert various date formats to ISO 8601 format: "YYYY-MM-DDTHH:MM:SS.000Z"
    
    Args:
        date_input: Date string in various formats
        timezone_offset: Timezone offset in hours (default: 0 for UTC)
    
    Returns:
        ISO 8601 formatted string or None if invalid
    """
    
    if not date_input or str(date_input).strip() == "" or str(date_input).lower() == "none":
        return None
    
    date_input = str(date_input).strip()
    
    try:
        if re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$', date_input):
            return date_input
        
        if re.match(r'^\d{10}$', date_input):
            dt = datetime.utcfromtimestamp(int(date_input))
            return dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        elif re.match(r'^\d{13}$', date_input):
            dt = datetime.utcfromtimestamp(int(date_input) / 1000)
            return dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        
        format_mappings = [
            (r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z?$', None, False),
            (r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$', "%Y-%m-%dT%H:%M:%S", False),
            (r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$', "%Y-%m-%d %H:%M:%S", False),
            (r'^\d{4}-\d{2}-\d{2}$', "%Y-%m-%d", True),
            (r'^\d{1,2} [A-Za-z]{3,4} \d{4}$', "%d %b %Y", True),  # New format: "17 Sept 2025"
            (r'^[A-Za-z]{3} \d{1,2}, \d{4}$', "%b %d, %Y", True),
            (r'^[A-Za-z]{3} \d{1,2}, \d{4} \d{2}:\d{2}$', "%b %d, %Y %H:%M", False),
            (r'^[A-Za-z]{3} \d{1,2}, \d{4} \d{2}:\d{2}:\d{2}$', "%b %d, %Y %H:%M:%S", False),
            (r'^[A-Za-z]+ \d{1,2}, \d{4}$', "%B %d, %Y", True),
            (r'^[A-Za-z]+ \d{1,2}, \d{4} \d{2}:\d{2}$', "%B %d, %Y %H:%M", False),
            (r'^[A-Za-z]+ \d{1,2}, \d{4} \d{2}:\d{2}:\d{2}$', "%B %d, %Y %H:%M:%S", False),
            (r'^\d{1,2}/\d{1,2}/\d{4}$', "%m/%d/%Y", True),
            (r'^\d{1,2}/\d{1,2}/\d{4} \d{2}:\d{2}$', "%m/%d/%Y %H:%M", False),
            (r'^\d{1,2}/\d{1,2}/\d{4} \d{2}:\d{2}:\d{2}$', "%m/%d/%Y %H:%M:%S", False),
            (r'^\d{4}/\d{1,2}/\d{1,2}$', "%Y/%m/%d", True),
            (r'^\d{4}/\d{1,2}/\d{1,2} \d{2}:\d{2}$', "%Y/%m/%d %H:%M", False),
            (r'^\d{4}/\d{1,2}/\d{1,2} \d{2}:\d{2}:\d{2}$', "%Y/%m/%d %H:%M:%S", False),
        ]
        
        for pattern, format_str, is_date_only in format_mappings:
            if re.match(pattern, date_input):
                try:
                    # Special handling for "17 Sept 2025" format - normalize "Sept" to "Sep"
                    if format_str == "%d %b %Y" and " Sept " in date_input:
                        date_input = date_input.replace(" Sept ", " Sep ")
                    
                    if format_str is None:
                        # Handle ISO format with or without microseconds
                        if not date_input.endswith('Z'):
                            date_input += 'Z'
                        # Normalize to 3-digit milliseconds format
                        if 'T' in date_input and '.' in date_input:
                            # Extract the fractional seconds part and normalize to 3 digits
                            parts = date_input.split('.')
                            if len(parts) == 2:
                                seconds_part = parts[1].rstrip('Z')
                                # Truncate or pad to 3 digits
                                if len(seconds_part) > 3:
                                    seconds_part = seconds_part[:3]
                                elif len(seconds_part) < 3:
                                    seconds_part = seconds_part.ljust(3, '0')
                                date_input = f"{parts[0]}.{seconds_part}Z"
                        elif 'T' in date_input and '.' not in date_input:
                            date_input = date_input.replace('Z', '.000Z')
                        return date_input
                    
                    dt = datetime.strptime(date_input, format_str)
                    
                    if is_date_only:
                        dt = dt.replace(hour=6, minute=0, second=0)
                    
                    if timezone_offset != 0:
                        dt = dt + timedelta(hours=timezone_offset)
                    
                    return dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")
                    
                except ValueError as e:
                    logger.debug(f"Failed to parse '{date_input}' with format '{format_str}': {e}")
                    continue
        
        logger.warning(f"Could not parse date format: {date_input}")
        return None
        
    except Exception as e:
        logger.error(f"Error parsing date '{date_input}': {str(e)}")
        return None


def parse_relative_date(date_input: str) -> str:
    """
    Parse relative date expressions like "2 days ago", "1 week ago"
    
    Args:
        date_input: Relative date expression
        
    Returns:
        ISO 8601 formatted string
    """
    if not date_input:
        return normalize_datetime("")
    
    date_input = date_input.lower().strip()
    now = datetime.utcnow()
    
    relative_patterns = {
        r'(\d+)\s*days?\s*ago': lambda x: now - timedelta(days=int(x)),
        r'(\d+)\s*weeks?\s*ago': lambda x: now - timedelta(weeks=int(x)),
        r'(\d+)\s*months?\s*ago': lambda x: now - timedelta(days=int(x)*30),
        r'(\d+)\s*years?\s*ago': lambda x: now - timedelta(days=int(x)*365),
        r'(\d+)\s*hours?\s*ago': lambda x: now - timedelta(hours=int(x)),
        r'(\d+)\s*minutes?\s*ago': lambda x: now - timedelta(minutes=int(x)),
        r'yesterday': lambda x: now - timedelta(days=1),
        r'today': lambda x: now,
    }
    
    for pattern, calc_func in relative_patterns.items():
        match = re.search(pattern, date_input)
        if match:
            try:
                if pattern in ['yesterday', 'today']:
                    dt = calc_func(None)
                else:
                    dt = calc_func(match.group(1))
                return dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")
            except Exception as e:
                logger.error(f"Error calculating relative date '{date_input}': {str(e)}")
                break
    
    return normalize_datetime(date_input)


def get_date_only(date_input: Union[str, None]) -> Union[str, None]:
    """
    Convert various date formats to date-only format: "YYYY-MM-DD"
    
    Args:
        date_input: Date string in various formats
        
    Returns:
        Date string in "YYYY-MM-DD" format, or None if parsing fails
    """
    if not date_input:
        return None
    
    # First normalize to full ISO format
    normalized = normalize_datetime(date_input)
    if not normalized:
        return None
    
    # Extract just the date part (first 10 characters: YYYY-MM-DD)
    return normalized[:10]


def generate_timestamp() -> str:
    """
    Generate unique timestamp in format: YYYYMMDD_HHMMSS_microseconds
    
    Returns:
        Unique timestamp string for file naming
    """
    current_time = datetime.now()
    return current_time.strftime("%Y%m%d_%H%M%S_%f")


def get_current_iso_time() -> str:
    """
    Get current time in ISO 8601 format
    
    Returns:
        Current time in ISO 8601 format
    """
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")


def get_current_collected_at() -> str:
    """
    Get current time for collected_at field (ISO format with microseconds)
    
    Returns:
        Current time in ISO format for collected_at timestamps
    """
    return datetime.now().isoformat()


def validate_iso_datetime(date_string: str) -> bool:
    """
    Validate if string is in valid ISO 8601 format
    
    Args:
        date_string: String to validate
        
    Returns:
        True if valid ISO 8601 format
    """
    try:
        pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$'
        return bool(re.match(pattern, date_string))
    except Exception:
        return False