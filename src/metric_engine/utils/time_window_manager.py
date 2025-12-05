"""
Time window management utilities.
"""

from datetime import datetime, timedelta
from typing import List, Optional
from ..models import TimeWindow


class TimeWindowManager:
    """Manages time window calculations and operations."""
    
    def __init__(self, window_configs: List[dict]):
        """
        Initialize time window manager.
        
        Args:
            window_configs: List of window configurations with 'name' and 'duration_seconds'
        """
        self.windows = {}
        for config in window_configs:
            if config.get("enabled", True):
                self.windows[config["name"]] = config["duration_seconds"]
    
    def get_window_for_timestamp(
        self, 
        timestamp: datetime, 
        window_name: str
    ) -> Optional[TimeWindow]:
        """
        Get time window for a given timestamp.
        
        Args:
            timestamp: The timestamp to find window for
            window_name: Name of the window type (e.g., "5min", "hourly")
            
        Returns:
            TimeWindow object or None if window not found
        """
        if window_name not in self.windows:
            return None
        
        duration_seconds = self.windows[window_name]
        window_start = self._round_to_window(timestamp, duration_seconds)
        window_end = window_start + timedelta(seconds=duration_seconds)
        
        return TimeWindow(
            name=window_name,
            duration_seconds=duration_seconds,
            start_time=window_start,
            end_time=window_end,
            enabled=True
        )
    
    def _round_to_window(self, timestamp: datetime, duration_seconds: int) -> datetime:
        """
        Round timestamp down to the start of the time window.
        
        Args:
            timestamp: The timestamp to round
            duration_seconds: Window duration in seconds
            
        Returns:
            Rounded timestamp
        """
        # For 5-minute windows
        if duration_seconds == 300:
            return timestamp.replace(minute=(timestamp.minute // 5) * 5, second=0, microsecond=0)
        
        # For hourly windows
        elif duration_seconds == 3600:
            return timestamp.replace(minute=0, second=0, microsecond=0)
        
        # For daily windows
        elif duration_seconds == 86400:
            return timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # For weekly windows (round to Monday 00:00)
        elif duration_seconds == 604800:
            days_since_monday = timestamp.weekday()
            return (timestamp - timedelta(days=days_since_monday)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        
        # For custom windows, round down to nearest duration
        else:
            epoch = timestamp.timestamp()
            rounded_epoch = (epoch // duration_seconds) * duration_seconds
            return datetime.fromtimestamp(rounded_epoch, tz=timestamp.tzinfo).replace(
                microsecond=0
            )
    
    def get_windows_for_range(
        self,
        start_time: datetime,
        end_time: datetime,
        window_name: str
    ) -> List[TimeWindow]:
        """
        Get all time windows that overlap with the given time range.
        
        Args:
            start_time: Start of the range
            end_time: End of the range
            window_name: Name of the window type
            
        Returns:
            List of TimeWindow objects
        """
        if window_name not in self.windows:
            return []
        
        duration_seconds = self.windows[window_name]
        windows = []
        current = self._round_to_window(start_time, duration_seconds)
        end = self._round_to_window(end_time, duration_seconds)
        
        while current <= end:
            window = TimeWindow(
                name=window_name,
                duration_seconds=duration_seconds,
                start_time=current,
                end_time=current + timedelta(seconds=duration_seconds),
                enabled=True
            )
            windows.append(window)
            current += timedelta(seconds=duration_seconds)
        
        return windows
    
    def get_window_duration(self, window_name: str) -> Optional[int]:
        """Get duration in seconds for a window name."""
        return self.windows.get(window_name)

