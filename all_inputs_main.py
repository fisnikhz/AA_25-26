import os
from parser.all_inputs_parser import parse_all_files

DATA_FOLDER = "data\\input"

def main():
    if not os.path.isdir(DATA_FOLDER):
        print(f"Folder '{DATA_FOLDER}' does not exist.")
        return
    
    all_instances = parse_all_files(DATA_FOLDER)

    for file_name, instance in all_instances:
        print(f"\nParsing file: {file_name}")
        print(f"Opening time: {instance.opening_time}")
        print(f"Closing time: {instance.closing_time}")
        print(f"Number of channels: {len(instance.channels)}")
        for ch in instance.channels:
            print(f"  Channel {ch.channel_id} ({ch.channel_name}):")
            for p in ch.programs:
                print(f"    {p.program_id} | {p.start}-{p.end} | {p.genre} | Score: {p.score}")

if __name__ == "__main__":
    main()