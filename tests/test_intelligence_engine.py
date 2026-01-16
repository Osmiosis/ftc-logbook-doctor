
import pytest
import pandas as pd
from datetime import datetime, timedelta
from src.diagnostics.intelligence_engine import diagnose_issues, generate_diagnosis_summary


def create_test_dataframe_with_battery_issues():
    """fake battery problems"""
    base_time = datetime(2026, 1, 16, 10, 0, 0)
    
    data = []
    
    # Normal happenings
    for i in range(5):
        data.append({
            'entry_id': i + 1,
            'datetime': base_time + timedelta(seconds=i*2),
            'timestamp': f'01-16 10:00:{i*2:02d}.000',
            'pid': 1234,
            'tid': 5678,
            'level': 'I',
            'tag': 'RobotCore',
            'message': f'Battery voltage: {13.2 - i*0.1}V',
            'battery_voltage': 13.2 - i*0.1,
            'loop_time_ms': None,
            'is_disconnect': False
        })
    
    # High current thing happened
    data.append({
        'entry_id': 6,
        'datetime': base_time + timedelta(seconds=10),
        'timestamp': '01-16 10:00:10.000',
        'pid': 1234,
        'tid': 5678,
        'level': 'W',
        'tag': 'RobotCore',
        'message': 'could not read Motor Controller: comm timeout',
        'battery_voltage': None,
        'loop_time_ms': None,
        'is_disconnect': False
    })
    
    data.append({
        'entry_id': 7,
        'datetime': base_time + timedelta(seconds=10, milliseconds=100),
        'timestamp': '01-16 10:00:10.100',
        'pid': 1234,
        'tid': 5678,
        'level': 'W',
        'tag': 'RobotCore',
        'message': 'Battery voltage: 11.5V - CRITICAL',
        'battery_voltage': 11.5,
        'loop_time_ms': None,
        'is_disconnect': False
    })
    
    # Low battery issue
    for i in range(3):
        data.append({
            'entry_id': 8 + i,
            'datetime': base_time + timedelta(seconds=12 + i*2),
            'timestamp': f'01-16 10:00:{12 + i*2:02d}.000',
            'pid': 1234,
            'tid': 5678,
            'level': 'W',
            'tag': 'RobotCore',
            'message': f'Battery voltage: {11.5 - i*0.05}V',
            'battery_voltage': 11.5 - i*0.05,
            'loop_time_ms': None,
            'is_disconnect': False
        })
    
    return pd.DataFrame(data)


def test_diagnose_high_current_event():
    """Detect high current happenings"""
    df = create_test_dataframe_with_battery_issues()
    result = diagnose_issues(df)
    
    assert len(result.high_current_events) > 0

    assert len(result.critical_issues) > 0

    assert result.health_score < 100


def test_battery_prediction():
    """Testing of the battery life prediction stuff"""
    df = create_test_dataframe_with_battery_issues()
    result = diagnose_issues(df)

    assert result.battery_prediction is not None

    assert result.battery_prediction['predicted_voltage_at_150s'] < 13.0


def test_generate_diagnosis_summary():
    df = create_test_dataframe_with_battery_issues()
    result = diagnose_issues(df)
    summary = generate_diagnosis_summary(result)
    
    assert "Doctor's Diagnosis" in summary
    assert "Robot Health Score" in summary
    assert "Pit Crew Action Items" in summary
   
    assert len(result.recommendations) > 0


def test_empty_dataframe():
    df = pd.DataFrame()
    result = diagnose_issues(df)
    
    assert result.health_score == 100
    assert len(result.critical_issues) == 0


def test_health_score_calculation():
    """health score calc"""
    df = create_test_dataframe_with_battery_issues()
    result = diagnose_issues(df)
    
    assert 0 <= result.health_score <= 100
    
    if len(result.critical_issues) > 0:
        assert result.health_score < 100
