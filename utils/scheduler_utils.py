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