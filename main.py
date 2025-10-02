#!/usr/bin/env python3 

from parser.file_selector import select_file
from parser.parser import Parser
from scheduler.scheduler import schedule_channels
from serializer.serializer import SolutionSerializer

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
    
    schedule_list = schedule_channels(instance)
    
    print("\nSchedule:")
    for schedule in schedule_list:
        print(f"Channel {schedule.channel_index}: {schedule.start_time}-{schedule.end_time}")
    
    serializer = SolutionSerializer()
    serializer.serialize(schedule_list)

if __name__ == "__main__":
    main()
