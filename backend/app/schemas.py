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
    allowed_classes: list[int] = Field(default=[10,11], min_length=1, max_length=11)
    ranking_visible: bool = False
    @model_validator(mode='after')
    def valid(self):
        if self.registration_start.tzinfo is None or self.registration_end.tzinfo is None: raise ValueError('Укажите часовой пояс')
        if self.registration_end <= self.registration_start: raise ValueError('Некорректный период')
        if self.type=='SCHOOL' and (any(c not in (10,11) for c in self.allowed_classes) or len(set(self.allowed_classes))!=len(self.allowed_classes)): raise ValueError('Для школьников доступны только 10 и 11 классы без повторений')
        return self

class StageInput(Strict):
    title: str = Field(min_length=1, max_length=150)
    kind: Literal['qualifying','main']
    starts_at: datetime
    ends_at: datetime
    duration_minutes: int = Field(ge=1, le=1440)
    story_intro: str = Field(default='', max_length=10000)
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
    academy_chapter: int | None = Field(default=None, ge=1, le=14)
    kind: Literal['code','choice','text'] = 'code'
    position: int = Field(default=0, ge=0, le=1000)
    answer_options: list[str] = Field(default_factory=list, max_length=8)
    correct_option: int | None = Field(default=None, ge=0, le=7)
    rubric: str = Field(default='', max_length=10000)
    tests: list[CaseInput] = Field(default_factory=list, max_length=50)
    @model_validator(mode='after')
    def valid_type(self):
        if self.kind!='code' and self.academy_chapter is not None:raise ValueError('Номер главы назначается только задаче на Python')
        if self.kind=='code':
            if not self.tests: raise ValueError('Для задачи на Python добавьте хотя бы один тест')
            if self.answer_options or self.correct_option is not None or self.rubric: raise ValueError('У задачи на Python не должно быть настройки контрольного вопроса')
        elif self.kind=='choice':
            self.answer_options=[s.strip() for s in self.answer_options]
            if not 2<=len(self.answer_options)<=8 or any(not s or len(s)>1000 for s in self.answer_options) or len(set(self.answer_options))!=len(self.answer_options): raise ValueError('Укажите от 2 до 8 непустых различных вариантов ответа')
            if self.correct_option is None or self.correct_option>=len(self.answer_options): raise ValueError('Выберите правильный вариант')
            if self.tests or self.rubric: raise ValueError('Для выбора ответа тесты и критерии ручной оценки не используются')
        else:
            if self.tests or self.answer_options or self.correct_option is not None: raise ValueError('Для развёрнутого ответа не нужны тесты и варианты')
        return self

class AnswerInput(Strict):
    answer: str = Field(default='', max_length=10000)
    option_index: int | None = Field(default=None, ge=0, le=7)

class ReviewInput(Strict):
    score: int = Field(ge=0, le=1000)
    feedback: str = Field(default='', max_length=5000)

class TaskFocusInput(Strict):
    task_id: str | None = Field(default=None, max_length=36)

class AcademyInput(Strict):
    type: Literal['SCHOOL','SPO']

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
