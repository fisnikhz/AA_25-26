#!/usr/bin/env python3 

from parser.file_selector import select_file
from parser.parser import Parser
from scheduler.scheduler import schedule_channels
# from models.solution import Schedule
# from serializer.serializer import SolutionSerializer

def main():
    file_path = select_file()
    parser = Parser(file_path)
    instance = parser.parse()

    # Simulim i schedules
    #
    # serializer = SolutionSerializer()
    # serializer.serialize(schedule_list)

    print("\nOpening time:", instance.opening_time)
    print("Closing time:", instance.closing_time)
    print("Channels:")
    for ch in instance.channels:
        print(f"  Channel {ch.channel_name}:")
        for p in ch.programs:
            print(f"    {p.program_id} | {p.start}-{p.end} | {p.genre} | Score: {p.score}")

    # qikjo o qitu veq per arsye zhvilluse, fshije ma von
    print(instance)
    
    schedule_channels(instance)

if __name__ == "__main__":
    main()
