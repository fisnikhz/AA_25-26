from typing import List

from models.channel import Channel
from models.instance_data import InstanceData


class Utils:

    @staticmethod
    def get_channel_program_by_time(channel : Channel, time: int):
        for program in channel.programs:
            if program.start <= time < program.end:
                return program

    @staticmethod
    def get_program_by_unique_id(instance_data: InstanceData, unique_id: str):
        for channel in instance_data.channels:
            for program in channel.programs:
                if program.unique_id == unique_id:
                    return program


