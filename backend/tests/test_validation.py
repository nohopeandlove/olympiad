import pytest
from pydantic import ValidationError
from app.schemas import Register, TaskInput, StageInput

def test_no_mentor_fields():
    with pytest.raises(ValidationError):
        Register(olympiad_id='1',email='a@example.org',password='longPassword12',confirm_password='longPassword12',last_name='А',first_name='Б',birth_date='2008-01-01',phone='+79001234567',region='Р',city='Г',organization='О',consent_data=True,consent_rules=True,mentor_email='x@example.org')

def test_resource_limits():
    for limits in [{'time_limit':999},{'memory_limit':9999}]:
        with pytest.raises(ValidationError):TaskInput(title='T',statement='T',tests=[{'input':'','expected':''}],**limits)

def test_stage_timezone_required():
    with pytest.raises(ValidationError):StageInput(title='T',kind='main',starts_at='2026-10-01T00:00:00',ends_at='2026-10-02T00:00:00',duration_minutes=60)
