from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel, Field, EmailStr, ConfigDict, model_validator

class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)

class Register(Strict):
    olympiad_id: str
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    confirm_password: str
    last_name: str = Field(min_length=1, max_length=100)
    first_name: str = Field(min_length=1, max_length=100)
    middle_name: str = Field(default='', max_length=100)
    birth_date: date
    phone: str = Field(pattern=r'^\+?[0-9 ()-]{7,30}$')
    region: str = Field(min_length=1, max_length=150)
    city: str = Field(min_length=1, max_length=150)
    organization: str = Field(min_length=1, max_length=300)
    school_class: int | None = None
    course: int | None = None
    group: str = Field(default='', max_length=100)
    consent_data: bool
    consent_rules: bool
    @model_validator(mode='after')
    def valid(self):
        if self.password != self.confirm_password: raise ValueError('Пароли не совпадают')
        if not self.consent_data or not self.consent_rules: raise ValueError('Необходимо согласие')
        if self.birth_date >= date.today(): raise ValueError('Некорректная дата рождения')
        return self

class Join(Strict):
    school_class: int | None = None
    course: int | None = None
    group: str = Field(default='', max_length=100)
    consent_data: bool
    consent_rules: bool

class Login(Strict):
    email: EmailStr
    password: str = Field(max_length=128)

class OlympiadInput(Strict):
    type: Literal['SCHOOL','SPO']
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default='', max_length=20000)
    rules: str = Field(default='', max_length=50000)
    status: Literal['draft','scheduled','active','finished'] = 'draft'
    registration_start: datetime
    registration_end: datetime
    allowed_classes: list[int] = Field(default=[7,8,9,10,11], max_length=11)
    ranking_visible: bool = False
    @model_validator(mode='after')
    def valid(self):
        if self.registration_start.tzinfo is None or self.registration_end.tzinfo is None: raise ValueError('Укажите часовой пояс')
        if self.registration_end <= self.registration_start: raise ValueError('Некорректный период')
        if any(c not in range(1,12) for c in self.allowed_classes): raise ValueError('Некорректный класс')
        return self

class StageInput(Strict):
    title: str = Field(min_length=1, max_length=150)
    kind: Literal['qualifying','main']
    starts_at: datetime
    ends_at: datetime
    duration_minutes: int = Field(ge=1, le=1440)
    @model_validator(mode='after')
    def valid(self):
        if self.starts_at.tzinfo is None or self.ends_at.tzinfo is None: raise ValueError('Укажите часовой пояс')
        if self.ends_at <= self.starts_at: raise ValueError('Некорректный период')
        return self

class CaseInput(Strict):
    input: str = Field(max_length=100000)
    expected: str = Field(max_length=100000)
    public: bool = False

class TaskInput(Strict):
    title: str = Field(min_length=1, max_length=200)
    statement: str = Field(min_length=1, max_length=50000)
    input_description: str = Field(default='', max_length=10000)
    output_description: str = Field(default='', max_length=10000)
    constraints: str = Field(default='', max_length=10000)
    difficulty: str = Field(default='normal', max_length=30)
    time_limit: int = Field(default=2, ge=1, le=10)
    memory_limit: int = Field(default=128, ge=32, le=256)
    points: int = Field(default=100, ge=1, le=1000)
    tests: list[CaseInput] = Field(min_length=1, max_length=50)

class CodeInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    code: str = Field(min_length=1, max_length=50000)
    mode: Literal['run','submit'] = 'submit'

class DraftInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    code: str = Field(max_length=50000)

class EventInput(Strict):
    event_type: Literal['COPY_ATTEMPT','PASTE_ATTEMPT','CONTEXT_MENU','TAB_HIDDEN','WINDOW_BLUR','FULLSCREEN_EXIT','CONNECTION_LOST','OTHER']
    metadata: dict[str,str] = Field(default_factory=dict, max_length=10)

class ParticipantInput(Strict):
    status: Literal['registered','blocked','disqualified']
    organization: str = Field(min_length=1, max_length=300)
    school_class: int | None = None
    course: int | None = None
    group: str = Field(default='', max_length=100)
