"""
Unit tests for date utilities.
"""

import pytest
import time
import datetime
from utils.date_utils import (
    get_current_timestamp, format_timestamp, parse_timestamp,
    get_date_from_timestamp, get_timestamp_from_date, get_time_ago
)

class TestDateUtils:
    """Tests for date utilities."""
    
    @pytest.mark.unit
    def test_get_current_timestamp(self):
        """Test get_current_timestamp function."""
        # Get the current timestamp
        timestamp = get_current_timestamp()
        
        # Check that it's a valid timestamp
        assert isinstance(timestamp, int)
        assert timestamp > 0
        
        # Check that it's close to the current time
        assert abs(timestamp - int(time.time())) < 2
    
    @pytest.mark.unit
    def test_format_timestamp(self):
        """Test format_timestamp function."""
        # Test with a specific timestamp
        timestamp = 1609459200  # 2021-01-01 00:00:00 UTC
        
        # Test with default format
        assert format_timestamp(timestamp) == "2021-01-01 00:00:00"
        
        # Test with custom format
        assert format_timestamp(timestamp, "%Y-%m-%d") == "2021-01-01"
        assert format_timestamp(timestamp, "%H:%M:%S") == "00:00:00"
        
        # Test with invalid timestamp
        assert format_timestamp("not-a-timestamp") == ""
        assert format_timestamp(None) == ""
    
    @pytest.mark.unit
    def test_parse_timestamp(self):
        """Test parse_timestamp function."""
        # Test with a specific date string
        date_str = "2021-01-01 00:00:00"
        
        # Test with default format
        assert parse_timestamp(date_str) == 1609459200
        
        # Test with custom format
        assert parse_timestamp("2021-01-01", "%Y-%m-%d") == 1609459200
        
        # Test with invalid date string
        assert parse_timestamp("not-a-date") is None
        assert parse_timestamp(None) is None
    
    @pytest.mark.unit
    def test_get_date_from_timestamp(self):
        """Test get_date_from_timestamp function."""
        # Test with a specific timestamp
        timestamp = 1609459200  # 2021-01-01 00:00:00 UTC
        
        # Get the date
        date = get_date_from_timestamp(timestamp)
        
        # Check that it's a valid date
        assert isinstance(date, datetime.datetime)
        assert date.year == 2021
        assert date.month == 1
        assert date.day == 1
        assert date.hour == 0
        assert date.minute == 0
        assert date.second == 0
        
        # Test with invalid timestamp
        assert get_date_from_timestamp("not-a-timestamp") is None
        assert get_date_from_timestamp(None) is None
    
    @pytest.mark.unit
    def test_get_timestamp_from_date(self):
        """Test get_timestamp_from_date function."""
        # Test with a specific date
        date = datetime.datetime(2021, 1, 1, 0, 0, 0)
        
        # Get the timestamp
        timestamp = get_timestamp_from_date(date)
        
        # Check that it's a valid timestamp
        assert isinstance(timestamp, int)
        assert timestamp == 1609459200
        
        # Test with invalid date
        assert get_timestamp_from_date("not-a-date") is None
        assert get_timestamp_from_date(None) is None
    
    @pytest.mark.unit
    def test_get_time_ago(self):
        """Test get_time_ago function."""
        # Get the current timestamp
        now = int(time.time())
        
        # Test with different time periods
        assert get_time_ago(now) == "0 seconds ago"
        assert get_time_ago(now - 30) == "30 seconds ago"
        assert get_time_ago(now - 60) == "1 minute ago"
        assert get_time_ago(now - 120) == "2 minutes ago"
        assert get_time_ago(now - 3600) == "1 hour ago"
        assert get_time_ago(now - 7200) == "2 hours ago"
        assert get_time_ago(now - 86400) == "1 day ago"
        assert get_time_ago(now - 172800) == "2 days ago"
        assert get_time_ago(now - 604800) == "1 week ago"
        assert get_time_ago(now - 1209600) == "2 weeks ago"
        assert get_time_ago(now - 2592000) == "1 month ago"
        assert get_time_ago(now - 5184000) == "2 months ago"
        assert get_time_ago(now - 31536000) == "1 year ago"
        assert get_time_ago(now - 63072000) == "2 years ago"
        
        # Test with future timestamp
        assert get_time_ago(now + 3600) == "in the future"
        
        # Test with invalid timestamp
        assert get_time_ago("not-a-timestamp") == "unknown time ago"
        assert get_time_ago(None) == "unknown time ago"
