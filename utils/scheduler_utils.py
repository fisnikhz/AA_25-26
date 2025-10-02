from typing import List

from models.instance_data import InstanceData
from models.schedule import Schedule
from validator.validator import Validator
from utils.utils import Utils


class SchedulerUtils:
    # @staticmethod
    # def find_best_channel_to_play(schedule, instance, time):
    # valid_channels = get_valid_schedules(schedule, instance, time)
    # max_score = 0
    # best_channel = None
    # for channel in valid_channels:
    #     program = Utils.get_channel_program_by_time(instance.channels[channel], time)
    #     if program and program.score > max_score:
    #         max_score = program.score + calculate_bonus_score() -  calculate_penalty_score()
    #         best_channel = channel
    # return best_channel, score
    
    @staticmethod
    def switch_channel(schedule_plan: List[Schedule], channel_index: int, start_time: int, end_time: int):
        schedule_plan.append(Schedule(
            channel_index=channel_index,
            start_time=start_time,
            end_time=end_time,
            unique_program_id=f"{channel_index}_{start_time}_{end_time}"
        ))

    @staticmethod
    def get_valid_schedules(schedule_plan: List[Schedule], instance_data: InstanceData, schedule_time: int) -> List[
        int]:
        valid_channels = []

        for channel_index, _ in enumerate(instance_data.channels):
            if Validator.is_channel_valid(schedule_plan, instance_data, channel_index, schedule_time):
                valid_channels.append(channel_index)

        return valid_channels

    # -----------------------------------
    # --------- METODAT PRIVATE ---------
    # -----------------------------------



    @staticmethod
    def _calculate_bonus_score():
        # si kem renet per bonus/penalty score ni her
        return 0

    @staticmethod
    def _calculate_penalty_score():
        return 0