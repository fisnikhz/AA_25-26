from typing import List

from models.instance_data import InstanceData
from models.schedule import Schedule
from validator.validator import Validator


class SchedulerUtils:
    @staticmethod
    def get_valid_schedules(schedule_plan: List[Schedule], instance_data: InstanceData, schedule_time: int):
        valid_channels = []

        for channel_index, _ in enumerate(instance_data.channels):
            if Validator.is_channel_valid(schedule_plan, instance_data, channel_index, schedule_time):
                valid_channels.append(channel_index)

        return valid_channels

    @staticmethod
    def switch_channel(schedule_plan: List[Schedule], channel_index: int, start_time: int, end_time: int):
        schedule_plan.append(Schedule(
            channel_index=channel_index,
            start_time=start_time,
            end_time=end_time,
            unique_program_id=f"{channel_index}_{start_time}_{end_time}"
        ))

    @staticmethod
    def calculate_bonus_score(program, time):
        # For a basic working example, just return 0 as bonus score
        # You can enhance this later with time preferences
        return 0