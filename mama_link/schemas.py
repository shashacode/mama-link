"""Validation for the local synthetic-only API."""
from typing import Literal
from math import isfinite
from pydantic import BaseModel, ConfigDict, Field, StrictBool, field_validator, model_validator
from .core import load_cases

SYMPTOMS = sorted({key for case in load_cases() for key in case["symptoms"]})
RANGES = {"gestational_age": (0, 45), "postpartum_day": (0, 365),
          "systolic_bp": (40, 300), "diastolic_bp": (20, 200),
          "temperature": (30, 45), "heart_rate": (20, 250), "labour_duration": (0, 120)}


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Location(Model):
    state: str = Field(default="Ondo", max_length=80)
    lga: str = Field(default="", max_length=80)


class CaseInput(Model):
    synthetic: Literal[True]
    age: int | None = Field(default=None, ge=10, le=65, strict=True)
    pregnancy_stage: Literal["unknown", "first_trimester", "second_trimester", "third_trimester", "labour", "postpartum"]
    location: Location = Field(default_factory=Location)
    readings: dict[str, float | None] = Field(default_factory=dict)
    symptoms: dict[str, StrictBool] = Field(default_factory=dict)
    recent_glucose_screen_flagged: StrictBool = False
    notes: str = Field(default="", max_length=2000)

    @field_validator("synthetic", mode="before")
    @classmethod
    def require_explicit_synthetic(cls, value):
        if value is not True:
            raise ValueError("Explicit synthetic-data confirmation is required")
        return value

    @field_validator("readings", mode="before")
    @classmethod
    def validate_readings(cls, value):
        if not isinstance(value, dict):
            raise ValueError("readings must be an object")
        for key, number in value.items():
            if key not in RANGES:
                raise ValueError("Unknown measurement")
            if number is not None and (type(number) not in (int, float) or not isfinite(number)
                                       or not RANGES[key][0] <= number <= RANGES[key][1]):
                raise ValueError(f"Invalid {key} measurement")
        return value

    @field_validator("symptoms")
    @classmethod
    def validate_symptoms(cls, value):
        if set(value) - set(SYMPTOMS):
            raise ValueError("Unknown symptom: use the supported symptom checklist")
        return value

    def to_case(self):
        return {"case_id": "custom-demo", "age": self.age, "pregnancy_stage": self.pregnancy_stage,
                "location": self.location.model_dump(), "symptoms": self.symptoms,
                "readings": {key: {"value": value} for key, value in self.readings.items()},
                "history": {"recent_glucose_screen_flagged": self.recent_glucose_screen_flagged},
                "notes": self.notes}


class AssessmentInput(Model):
    import_id: str | None = Field(default=None, max_length=36)
    case_id: str | None = Field(default=None, pattern=r"^MAT-\d{3}$")
    case: CaseInput | None = None

    @model_validator(mode="after")
    def exactly_one(self):
        if (self.case_id is None) == (self.case is None):
            raise ValueError("Provide either a demo case ID or structured synthetic input")
        return self


class ConsentInput(Model):
    consent: Literal[True]
    facility_id: str = Field(pattern=r"^FAC-\d{3}$")

    @field_validator("consent", mode="before")
    @classmethod
    def require_explicit_consent(cls, value):
        if value is not True:
            raise ValueError("Explicit consent is required")
        return value


class Profile(Model):
    name: str = Field(min_length=1, max_length=80)
    age: int | None = Field(default=None, ge=10, le=65)
    pregnancy_stage: Literal['unknown', 'first_trimester', 'second_trimester', 'third_trimester', 'labour', 'postpartum'] = 'unknown'
    gestational_age: float | None = Field(default=None, ge=0, le=45)
    postpartum_day: int | None = Field(default=None, ge=0, le=365)
    state: str = Field(default='', max_length=80)
    place: str = Field(default='', max_length=80)
    language: Literal['en', 'pcm', 'yo', 'ig', 'ha'] = 'en'
    medications: str = Field(default='', max_length=500)
    allergies: str = Field(default='', max_length=500)
    synthetic: Literal[True]

    @field_validator('synthetic', mode='before')
    @classmethod
    def explicit_synthetic(cls, value):
        if value is not True:
            raise ValueError('Confirm fictional information explicitly')
        return value

    @field_validator('name')
    @classmethod
    def nonempty_name(cls, value):
        if not value.strip():
            raise ValueError('Enter a name')
        return value.strip()


class Credentials(Model):
    username: str = Field(pattern=r'^[a-zA-Z0-9_.-]{3,40}$')
    password: str = Field(min_length=10, max_length=128)


class Registration(Credentials):
    profile: Profile


class DeviceConsent(Model):
    enabled: StrictBool


class Measurement(Model):
    metric: Literal['systolic_bp', 'diastolic_bp', 'heart_rate', 'temperature']
    value: float
    unit: Literal['mmHg', 'bpm', 'C']
    measured_at: str = Field(max_length=40)

    @model_validator(mode='after')
    def valid_measurement(self):
        from datetime import datetime, timezone, timedelta
        units = {'systolic_bp': 'mmHg', 'diastolic_bp': 'mmHg', 'heart_rate': 'bpm', 'temperature': 'C'}
        if self.unit != units[self.metric] or not isfinite(self.value) or not RANGES[self.metric][0] <= self.value <= RANGES[self.metric][1]:
            raise ValueError('Invalid reading or unit')
        stamp = datetime.fromisoformat(self.measured_at.replace('Z', '+00:00'))
        if stamp.tzinfo is None or stamp > datetime.now(timezone.utc) + timedelta(minutes=5) or stamp < datetime.now(timezone.utc) - timedelta(hours=24):
            raise ValueError('Use a timezone-aware measurement from the past 24 hours')
        return self


class DeviceImport(Model):
    provider: Literal['apple_health', 'android_health_connect', 'other'] = 'other'
    source: Literal['sample_device', 'health_app_export']
    device_name: str = Field(min_length=1, max_length=80)
    measurements: list[Measurement] = Field(min_length=1, max_length=4)
    reviewed: Literal[True]
    synthetic: Literal[True]

    @field_validator('reviewed', 'synthetic', mode='before')
    @classmethod
    def explicit_confirmation(cls, value):
        if value is not True:
            raise ValueError('Explicit review and fictional-data confirmation are required')
        return value

    @model_validator(mode='after')
    def unique_metrics(self):
        if len({m.metric for m in self.measurements}) != len(self.measurements):
            raise ValueError('One reading per measurement is required')
        return self


class ChatTurn(Model):
    role: Literal['user', 'assistant']
    content: str = Field(min_length=1, max_length=5000)


class ChatInput(Model):
    message: str = Field(min_length=1, max_length=2000)
    share_context: StrictBool = False
    conversation: list[ChatTurn] = Field(default_factory=list, max_length=8)


class AppointmentInput(Model):
    assessment_id: str | None = Field(default=None, max_length=36)
    facility_id: str = Field(min_length=1, max_length=80)
    requested_for: str = Field(min_length=10, max_length=40)
    reason: str = Field(default="Follow-up review", max_length=300)


class AppointmentStatusInput(Model):
    status: Literal["confirmed", "cancelled", "missed", "completed"]


class FollowUpInput(Model):
    assessment_id: str | None = Field(default=None, max_length=36)
    task: str = Field(min_length=1, max_length=300)
    due_at: str = Field(min_length=10, max_length=40)


class FollowUpStatusInput(Model):
    status: Literal["acknowledged", "completed", "dismissed"]
