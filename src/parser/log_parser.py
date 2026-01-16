"""Android logcat only (I mean ftc only provides logcat only im pretty sure) """


import re
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional


class LogParser:
    
    LOGCAT_PATTERN = r'(\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3})\s+(\d+)[-\s](\d+)(?:/\?)?\s+([VDIWEF])[/\s]+([^:]+):\s+(.*)'
    BATTERY_PATTERN = r'battery.*?(\d+\.?\d*)\s*[vV]'
    LOOP_TIME_PATTERN = r'loop.*?(\d+\.?\d*)\s*ms'
    DISCONNECT_PATTERN = r'disconnect|connection\s+lost|device\s+not\s+found'
    
    def __init__(self):
        self.entries: List[Dict] = []
    
    def parse(self, log_content: str) -> pd.DataFrame:

        self.entries = []
        lines = log_content.split('\n')
        
        for line in lines:
            entry = self._parse_line(line)
            if entry:
                self.entries.append(entry)
        
        if not self.entries:
            return pd.DataFrame()
        
        df = pd.DataFrame(self.entries)
        df = self._enrich_data(df)
        
        return df
    
    def _parse_line(self, line: str) -> Optional[Dict]:

        match = re.match(self.LOGCAT_PATTERN, line)
        
        if not match:
            return None
        
        timestamp_str, pid, tid, level, tag, message = match.groups()
        
        entry = {
            'timestamp': timestamp_str,
            'pid': int(pid),
            'tid': int(tid),
            'level': level,
            'tag': tag.strip(),
            'message': message.strip(),
            'battery_voltage': None,
            'loop_time_ms': None,
            'is_disconnect': False
        }
        
        # battery stuff
        battery_match = re.search(self.BATTERY_PATTERN, message, re.IGNORECASE)
        if battery_match:
            entry['battery_voltage'] = float(battery_match.group(1))
        
        # loop time stuff
        loop_match = re.search(self.LOOP_TIME_PATTERN, message, re.IGNORECASE)
        if loop_match:
            entry['loop_time_ms'] = float(loop_match.group(1))
        
        # disconnection stuff
        if re.search(self.DISCONNECT_PATTERN, message, re.IGNORECASE):
            entry['is_disconnect'] = True
        
        return entry
    
    def _enrich_data(self, df: pd.DataFrame) -> pd.DataFrame:
    
        # timestamp to datetime + year cuz logcat lacks year info
        current_year = datetime.now().year
        df['datetime'] = pd.to_datetime(
            f"{current_year}-" + df['timestamp'],
            format='%Y-%m-%d %H:%M:%S.%f'
        )
        
        df = df.sort_values('datetime').reset_index(drop=True)
        
        df['entry_id'] = range(1, len(df) + 1)
        
        return df
    
    def get_battery_readings(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract only battery-related readings"""
        return df[df['battery_voltage'].notna()].copy()
    
    def get_loop_time_readings(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract only loop time readings"""
        return df[df['loop_time_ms'].notna()].copy()
    
    def get_disconnect_events(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract only disconnect events"""
        return df[df['is_disconnect'] == True].copy()
