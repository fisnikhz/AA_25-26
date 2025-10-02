#!/usr/bin/env python3

from models.channel import Channel
from models.instance_data import InstanceData
from models.priority_block import PriorityBlock
from models.program import Program
from models.schedule import Schedule
from parser.file_selector import select_file
from parser.parser import Parser
# from scheduler.scheduler import schedule_channels
from scheduler.greedy_scheduler import GreedyScheduler
from serializer.serializer import SolutionSerializer
from utils.scheduler_utils import SchedulerUtils
from utils.utils import Utils
# from models.solution import Schedule
# from serializer.serializer import SolutionSerializer
from validator.validator import Validator


def main():
    file_path = select_file()
    parser = Parser(file_path)
    instance = parser.parse()



    print("\nOpening time:", instance.opening_time)
    print("Closing time:", instance.closing_time)
    print("Channels:")
    for ch in instance.channels:
        print(f"  Channel {ch.channel_name}:")
        for p in ch.programs:
            print(f"    {p.program_id} | {p.start}-{p.end} | {p.genre} | Score: {p.score}")

    scheduler = GreedyScheduler(instance)
    solution = scheduler.generate_solution()

    print("\n Generated solution with total score: ", solution.total_score)

    output_file_name = SolutionSerializer.output_file_name_input()
    serializer = SolutionSerializer(output_file_name)
    serializer.serialize(solution)


if __name__ == "__main__":
    main()
