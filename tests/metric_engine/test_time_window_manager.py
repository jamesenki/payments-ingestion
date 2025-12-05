"""
Unit tests for time window manager.
"""

import pytest
from datetime import datetime, timedelta

from src.metric_engine.utils.time_window_manager import TimeWindowManager
from src.metric_engine.models import TimeWindow


class TestTimeWindowManager:
    """Tests for TimeWindowManager."""
    
    @pytest.fixture
    def window_configs(self):
        """Sample window configurations."""
        return [
            {"name": "5min", "duration_seconds": 300, "enabled": True},
            {"name": "hourly", "duration_seconds": 3600, "enabled": True},
            {"name": "daily", "duration_seconds": 86400, "enabled": True},
            {"name": "weekly", "duration_seconds": 604800, "enabled": False}
        ]
    
    @pytest.fixture
    def manager(self, window_configs):
        """Create a TimeWindowManager instance."""
        return TimeWindowManager(window_configs)
    
    def test_get_window_for_timestamp_5min(self, manager):
        """Test getting 5-minute window for timestamp."""
        timestamp = datetime(2025, 12, 5, 14, 23, 45)
        window = manager.get_window_for_timestamp(timestamp, "5min")
        
        assert window is not None
        assert window.name == "5min"
        assert window.duration_seconds == 300
        # Should round down to 14:20
        assert window.start_time.minute == 20
        assert window.start_time.second == 0
    
    def test_get_window_for_timestamp_hourly(self, manager):
        """Test getting hourly window for timestamp."""
        timestamp = datetime(2025, 12, 5, 14, 23, 45)
        window = manager.get_window_for_timestamp(timestamp, "hourly")
        
        assert window is not None
        assert window.name == "hourly"
        assert window.duration_seconds == 3600
        # Should round down to 14:00
        assert window.start_time.hour == 14
        assert window.start_time.minute == 0
        assert window.end_time.hour == 15
    
    def test_get_window_for_timestamp_daily(self, manager):
        """Test getting daily window for timestamp."""
        timestamp = datetime(2025, 12, 5, 14, 23, 45)
        window = manager.get_window_for_timestamp(timestamp, "daily")
        
        assert window is not None
        assert window.name == "daily"
        assert window.duration_seconds == 86400
        # Should round down to 00:00
        assert window.start_time.hour == 0
        assert window.start_time.minute == 0
    
    def test_get_window_for_timestamp_weekly(self, manager):
        """Test getting weekly window for timestamp."""
        # Friday, December 5, 2025
        # Note: weekly is disabled in config, so this will return None
        timestamp = datetime(2025, 12, 5, 14, 23, 45)
        window = manager.get_window_for_timestamp(timestamp, "weekly")
        
        # Weekly is disabled, so should return None
        assert window is None
    
    def test_get_window_for_timestamp_not_found(self, manager):
        """Test getting window that doesn't exist."""
        timestamp = datetime.now()
        window = manager.get_window_for_timestamp(timestamp, "nonexistent")
        
        assert window is None
    
    def test_get_window_for_timestamp_disabled(self, manager):
        """Test getting disabled window."""
        timestamp = datetime.now()
        # weekly is disabled in config
        window = manager.get_window_for_timestamp(timestamp, "weekly")
        
        # Should return None because it's disabled
        assert window is None
    
    def test_get_windows_for_range(self, manager):
        """Test getting all windows for a time range."""
        start_time = datetime(2025, 12, 5, 14, 0, 0)
        end_time = datetime(2025, 12, 5, 14, 15, 0)  # 15 minutes later
        
        windows = manager.get_windows_for_range(start_time, end_time, "5min")
        
        # Should have 4 windows: 14:00-14:05, 14:05-14:10, 14:10-14:15, 14:15-14:20
        # (includes window that contains end_time)
        assert len(windows) >= 3
        assert all(w.name == "5min" for w in windows)
    
    def test_get_windows_for_range_hourly(self, manager):
        """Test getting hourly windows for a range."""
        start_time = datetime(2025, 12, 5, 14, 0, 0)
        end_time = datetime(2025, 12, 5, 16, 0, 0)  # 2 hours later
        
        windows = manager.get_windows_for_range(start_time, end_time, "hourly")
        
        # Should have 3 windows: 14:00-15:00, 15:00-16:00, 16:00-17:00
        # (includes window that contains end_time)
        assert len(windows) >= 2
        assert windows[0].start_time.hour == 14
    
    def test_get_window_duration(self, manager):
        """Test getting window duration."""
        duration = manager.get_window_duration("5min")
        assert duration == 300
        
        duration = manager.get_window_duration("hourly")
        assert duration == 3600
        
        duration = manager.get_window_duration("nonexistent")
        assert duration is None
    
    def test_round_to_window_5min(self, manager):
        """Test rounding to 5-minute window."""
        timestamp = datetime(2025, 12, 5, 14, 23, 45)
        rounded = manager._round_to_window(timestamp, 300)
        
        assert rounded.minute == 20
        assert rounded.second == 0
        assert rounded.microsecond == 0
    
    def test_round_to_window_custom(self, manager):
        """Test rounding to custom window duration."""
        timestamp = datetime(2025, 12, 5, 14, 23, 45)
        # 15-minute window
        rounded = manager._round_to_window(timestamp, 900)
        
        # Should round down to nearest 15 minutes (14:15)
        assert rounded.minute == 15
        assert rounded.second == 0

