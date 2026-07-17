import uuid
from datetime import datetime, time
from typing import List, Optional, Dict, Any, Literal, Set
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field, field_validator, field_serializer, EmailStr, ConfigDict
from pydantic_core.core_schema import ValidationInfo

TTSType = Literal["ssugt", "yandex", "edge-tts"]
CategoriesType = Set[
    Literal["ru_mobile_numbers", "ru_city_numbers", "international_numbers"]
]


class LoginRequest(BaseModel):
    username: str
    password: str

class UserCreate(BaseModel):
    username: str
    password: str
    role: Literal["admin", "user", "owner"] = "user"

class UserResponse(BaseModel):
    id: uuid.UUID
    username: str
    role: str
    fullname: Optional[str] = None

    class Config:
        from_attributes = True
        
class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None

class UserPaginationResponse(BaseModel):
    items: List[UserResponse]
    total: int
    offset: int
    limit: int

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CallSchema(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    created_at: datetime
    is_paused: bool
    retry_limit: int
    schedule: List[Dict[str, Any]]
    tts_type: str
    categories: Set[str]
    phone_calls_count: int
    user: Optional[UserResponse] = None
    
    # === ДОБАВЛЯЕМ В OUTPUT-СХЕМУ ДЛЯ ОТОБРАЖЕНИЯ НА ФРОНТЕНДЕ ===
    control_call_number: Optional[str] = None
    control_call_interval: int
    control_call_enabled: bool
    
    email_report_address: Optional[str] = None
    email_report_interval: int
    email_report_enabled: bool
    
    email_report_trigger_start: bool
    email_report_trigger_interval: bool
    email_report_trigger_final: bool

    @field_validator("schedule", mode="after")
    @classmethod
    def reformat_schedule_times(cls, schedule: List[Dict[str, Any]]):
        if not schedule:
            return schedule

        def normalize_time(v: Any) -> Any:
            if v is None:
                return None
            if isinstance(v, time):
                return v.replace(second=0, microsecond=0).strftime("%H:%M")
            if isinstance(v, str):
                v = v.strip()
                for fmt in ("%H:%M:%S", "%H:%M"):
                    try:
                        t = datetime.strptime(v, fmt).time()
                        return t.replace(second=0, microsecond=0).strftime("%H:%M")
                    except ValueError:
                        pass
            return v

        for daily in schedule:
            for tr in daily.get("time_ranges", []):
                if "start_time_at" in tr:
                    tr["start_time_at"] = normalize_time(tr["start_time_at"])
                if "end_time_at" in tr:
                    tr["end_time_at"] = normalize_time(tr["end_time_at"])

        return schedule


class SynthesizeSchema(BaseModel):
    type_: TTSType = Field(default="ssugt", alias="type")
    text: str = Field(min_length=1)


class ScheduleSchema(BaseModel):
    schedule: List["CallDailyScheduleSchema"]

    @field_serializer("schedule")
    def serialize_schedule(self, schedule: List["CallDailyScheduleSchema"], _info):
        return [daily_schedule.model_dump(mode="json") for daily_schedule in schedule]

    @field_validator("schedule")
    def check_unique_weekdays(cls, v):
        weekdays = [item.weekday for item in v]
        if len(set(weekdays)) != len(weekdays):
            raise ValueError("Each weekday must appear only once in the schedule")
        return v


class PatchCallSchema(ScheduleSchema, BaseModel):
    name: str = Field(default="")
    is_paused: bool = Field(default=False)
    retry_limit: int = Field(default=0)
    schedule: List["CallDailyScheduleSchema"] = Field(default_factory=list)
    tts_type: TTSType = Field(default="ssugt")
    categories: CategoriesType = Field(default_factory=set)
    
    # === НОВЫЕ ПОЛЯ ДЛЯ PATCH ПОД МОДАЛКУ ===
    control_call_number: Optional[str] = Field(default=None)
    control_call_interval: Optional[int] = Field(default=None)
    control_call_enabled: Optional[bool] = Field(default=None)

    email_report_address: Optional[str] = Field(default=None)
    email_report_interval: Optional[int] = Field(default=None)
    email_report_enabled: Optional[bool] = Field(default=None)

    email_report_trigger_start: Optional[bool] = Field(default=None)
    email_report_trigger_interval: Optional[bool] = Field(default=None)
    email_report_trigger_final: Optional[bool] = Field(default=None)


class PhoneCallSchema(BaseModel):
    id: uuid.UUID
    phone_number: str
    synthesis: str
    duration: Optional[float]
    ringing_at: Optional[datetime]
    picked_up_at: Optional[datetime]
    completed_at: Optional[datetime]
    status: str
    cause: Optional[str]
    progress: Optional[float]
    retry_count: int

    @field_serializer("ringing_at", "picked_up_at", "completed_at")
    def serialize_dt(self, dt: Optional[datetime], _info):
        if dt is None:
            return None
        return dt.astimezone(ZoneInfo("Asia/Novosibirsk")).isoformat()


class OutgoingCallSchema(BaseModel):
    phone_number: str
    text: str


class CallTimeRangeSchema(BaseModel):
    start_time_at: time = Field(
        json_schema_extra={
            "title": "Start time",
            "description": "Start time of range",
            "examples": ["09:50"],
        }
    )
    end_time_at: time = Field(
        json_schema_extra={
            "title": "End time",
            "description": "End time of range",
            "examples": ["17:00"],
        }
    )
    max_num_channels_occupied: int
    
    @field_serializer("start_time_at", "end_time_at")
    def serialize_time_without_seconds(self, t: time, _info):
        return t.strftime("%H:%M")

    @field_validator("end_time_at")
    def check_time_order(cls, v, info: ValidationInfo):
        if "start_time_at" in info.data and v <= info.data["start_time_at"]:
            raise ValueError("end_time_at must be later than start_time_at")
        return v


class CallDailyScheduleSchema(BaseModel):
    weekday: Literal[
        "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"
    ]
    time_ranges: List[CallTimeRangeSchema]

    @field_validator("time_ranges")
    def check_no_overlaps(cls, ranges):
        sorted_ranges = sorted(ranges, key=lambda r: r.start_time_at)
        for prev, curr in zip(sorted_ranges, sorted_ranges[1:]):
            if prev.end_time_at > curr.start_time_at:
                raise ValueError("time_ranges must not overlap within the same weekday")
        return ranges


class OutgoingCallsSchema(ScheduleSchema, BaseModel):
    name: str
    calls: List[OutgoingCallSchema]
    is_paused: bool = Field(default=False)
    retry_limit: int = Field(default=3)
    schedule: List[CallDailyScheduleSchema]
    tts_type: TTSType = Field(default="ssugt")
    categories: CategoriesType = Field(
        default={"ru_mobile_numbers", "ru_city_numbers", "international_numbers"}
    )
    
    # === НАСТРОЙКИ ИЗ МОДАЛКИ ПРИ СОЗДАНИИ КАМПАНИИ ===
    control_call_number: Optional[str] = Field(default=None)
    control_call_interval: int = Field(default=50)
    control_call_enabled: bool = Field(default=False)

    email_report_address: Optional[str] = Field(default=None)
    email_report_interval: int = Field(default=100)
    email_report_enabled: bool = Field(default=False)

    email_report_trigger_start: bool = Field(default=False)
    email_report_trigger_interval: bool = Field(default=False)
    email_report_trigger_final: bool = Field(default=False)
    
class AuditLogCreate(BaseModel):
    userId: str
    username: str
    action_type: str
    action_description: str
    payload: Optional[Any] = None
    timestamp: datetime
    
class AuditLogRead(BaseModel):
    # Эта настройка критически важна! 
    # Она позволяет Pydantic читать данные прямо из объектов SQLAlchemy
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: Optional[str] = None
    username: Optional[str] = None
    action_type: str
    action_description: str
    payload: Optional[Any] = None
    ip_address: Optional[str] = None
    created_at: datetime
    
class AuditLogPaginationResponse(BaseModel):
    items: List[AuditLogRead]
    total: int
    offset: int
    limit: int