
import pytest
import pandas as pd
from src.parser.log_parser import LogParser


def test_parse_valid_logcat_line():
    """Test to make sure its logcat"""
    parser = LogParser()
    line = "01-16 10:30:45.123  1234  5678 I RobotCore: Battery voltage: 13.2V"
    
    result = parser._parse_line(line)
    
    assert result is not None
    assert result['timestamp'] == "01-16 10:30:45.123"
    assert result['pid'] == 1234
    assert result['tid'] == 5678
    assert result['level'] == 'I'
    assert result['tag'] == 'RobotCore'
    assert 'Battery voltage' in result['message']
    assert result['battery_voltage'] == 13.2


def test_parse_loop_time():
    parser = LogParser()
    line = "01-16 10:30:45.123  1234  5678 D OpMode: Loop time: 25.5 ms"
    
    result = parser._parse_line(line)
    
    assert result is not None
    assert result['loop_time_ms'] == 25.5


def test_parse_disconnect_event():
    parser = LogParser()
    line = "01-16 10:30:45.123  1234  5678 E Device: Connection lost to motor controller"
    
    result = parser._parse_line(line)
    
    assert result is not None
    assert result['is_disconnect'] == True


def test_parse_multiple_lines():
    parser = LogParser()
    log_content = """01-16 10:30:45.123  1234  5678 I RobotCore: Battery voltage: 13.2V
01-16 10:30:45.150  1234  5678 D OpMode: Loop time: 25.5 ms
01-16 10:30:45.200  1234  5678 E Device: Connection lost"""
    
    df = parser.parse(log_content)
    
    assert len(df) == 3
    assert df['battery_voltage'].notna().sum() == 1
    assert df['loop_time_ms'].notna().sum() == 1
    assert df['is_disconnect'].sum() == 1


def test_parse_empty_content():
    parser = LogParser()
    df = parser.parse("")
    
    assert df.empty


def test_invalid_logcat_format():
    parser = LogParser()
    df = parser.parse("This is not a valid logcat format")
    
    assert df.empty
