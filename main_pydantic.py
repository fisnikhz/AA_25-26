import time
from parser.file_selector import select_file
from parser.parser_pydantic import PydanticParser


def main():
    file_path = select_file()

    start_time = time.time()
    parser = PydanticParser(file_path)
    instance = parser.parse()

    print("Opening time:", instance.opening_time)
    print("Closing time:", instance.closing_time)

    print(f"\n=== Channels ({len(instance.channels)}) ===")
    for ch in instance.channels:
        print(f"  Channel {ch.channel_id} ({ch.channel_name}):")
        for p in ch.programs:
            print(f"    {p.program_id} | {p.start}-{p.end} | {p.genre} | Score: {p.score}")

    end_time = time.time()
    execution_time = end_time - start_time
    print(f"\n=== Execution Time: {execution_time:.4f} seconds ===")
    
if __name__ == "__main__":
    main()
