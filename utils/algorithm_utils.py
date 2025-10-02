from typing import List

from models.channel import Channel
from models.instance_data import InstanceData
from models.program import Program
from models.schedule import Schedule
from utils.utils import Utils


class AlgorithmUtils:

    @staticmethod
    def get_best_fit(schedule_plan: List[Schedule], instance_data: InstanceData, schedule_time: int,
                     valid_channel_indexes: List[int]) ->  tuple[Channel, Program, int]:

        # returns best channel to pick at the time and what score will it provide if we switch to it

        max_score = 0
        best_channel = None
        best_program = None

        for channel_index in valid_channel_indexes:
            channel = instance_data.channels[channel_index]
            program = Utils.get_channel_program_by_time(channel, schedule_time)

            if not program:
                continue

            score = 0

            score += program.score
            score += AlgorithmUtils.get_time_preference_bonus(instance_data, program, schedule_time)
            score += AlgorithmUtils.get_switch_penalty(schedule_plan, instance_data, channel)
            score += AlgorithmUtils.get_delay_penalty(schedule_plan, instance_data, program, schedule_time)
            score += AlgorithmUtils.get_early_termination_penalty(schedule_plan, instance_data, program, schedule_time)

            if score > max_score:
                max_score = score
                best_channel = channel
                best_program = program

        return best_channel, best_program, max_score

    @staticmethod
    def get_time_preference_bonus(instance_data: InstanceData, program: Program, schedule_time: int):
        score = 0
        for preference in instance_data.time_preferences:
            if program.genre == preference.preferred_genre and preference.start <= schedule_time < preference.end:
                score += preference.bonus

        return score

    @staticmethod
    def get_switch_penalty(schedule_plan: List[Schedule], instance_data: InstanceData, channel: Channel):
        penalty = 0
        if not schedule_plan:
            return penalty

        last_schedule = schedule_plan[-1]
        if last_schedule.channel_id != channel.channel_id:
            penalty -= instance_data.switch_penalty

        return penalty

    @staticmethod
    def get_delay_penalty(schedule_plan: List[Schedule], instance_data: InstanceData, program: Program,
                          schedule_time: int):
        penalty = 0
        if not schedule_plan:
            return penalty

        last_schedule = schedule_plan[-1]

        if last_schedule.unique_program_id != program.unique_id and schedule_time > program.start:
            penalty -= instance_data.termination_penalty

        return penalty

    @staticmethod
    def get_early_termination_penalty(schedule_plan: List[Schedule], instance_data: InstanceData, program: Program,
                                      schedule_time: int):
        penalty = 0
        if not schedule_plan:
            return penalty

        last_schedule = schedule_plan[-1]

        if last_schedule.unique_program_id != program.unique_id and schedule_time < last_schedule.end_time:
            penalty -= instance_data.termination_penalty

        return penalty
