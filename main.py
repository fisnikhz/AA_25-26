from parser.file_selector import select_file
from parser.parser import Parser
from scheduler.greedy_scheduler import GreedyScheduler
from scheduler.greedy_lookahead import GreedyLookahead
from scheduler.beam_search import BeamSearchScheduler
from serializer.serializer import SolutionSerializer
from scheduler.beam_search_advanced import BeamSearchSchedulerAdvanced
from utils.utils import Utils


def main():
    file_path = select_file()
    parser = Parser(file_path)
    instance = parser.parse()
    Utils.set_current_instance(instance)

    print("\nOpening time:", instance.opening_time)
    print("Closing time:", instance.closing_time)
    print("Channels:")
    for ch in instance.channels:
        print(f"  Channel {ch.channel_name}:")
        for p in ch.programs:
            print(f"    {p.program_id} | {p.start}-{p.end} | {p.genre} | Score: {p.score}")

    print('\nChoose scheduler:')
    print('1: GreedyScheduler (original)')
    print('2: GreedyLookahead (lookahead greedy)')
    print('3: Beam_Search (bounded lookahead)')
    print('4: Beam_Search_Advanced (advanced lookahead)')
    choice = input('Select scheduler [1/2/3/4] (default 1): ').strip() or '1'

    if choice == '2':
        scheduler = GreedyLookahead(instance)
    elif choice == '3':
        scheduler = BeamSearchScheduler(instance)
    elif choice == '4':
        scheduler = BeamSearchSchedulerAdvanced(instance)
    else:
        scheduler = GreedyScheduler(instance)

    solution = scheduler.generate_solution()

    print(f"\n✓ Generated solution with total score: {solution.total_score}")

    # Konvertimi ne lowercase i emrit te algoritmit varesisht tipit te scheduler dhe percjellja te serializer
    algorithm_name = type(scheduler).__name__.lower()
    serializer = SolutionSerializer(input_file_path=file_path, algorithm_name=algorithm_name)
    serializer.serialize(solution)
    
    print(f"✓ Solution saved to output file")

if __name__ == "__main__":
    main()