from pydantic import BaseModel, model_validator
from typing import List, Optional


class Program(BaseModel):
    program_id: str
    start: int
    end: int
    genre: str
    score: int


class Channel(BaseModel):
    channel_id: int
    channel_name: Optional[str] = None
    programs: List[Program]


class PriorityBlock(BaseModel):
    start: int
    end: int
    allowed_channels: List[int]


class TimePreference(BaseModel):
    start: int
    end: int
    preferred_genre: str
    bonus: int


class InstanceData(BaseModel):
    opening_time: int
    closing_time: int
    min_duration: int
    max_consecutive_genre: int
    channels_count: int
    switch_penalty: int
    termination_penalty: int
    priority_blocks: List[PriorityBlock]
    time_preferences: List[TimePreference]
    channels: List[Channel]

    @model_validator(mode='after')
    def set_default_channel_names(self):
        for channel in self.channels:
            if channel.channel_name is None:
                channel.channel_name = f"Channel_{channel.channel_id}"
        return self
