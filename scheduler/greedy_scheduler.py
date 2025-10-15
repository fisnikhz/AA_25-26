from models.instance_data import InstanceData
from models.schedule import Schedule
from models.solution import Solution
from utils.algorithm_utils import AlgorithmUtils
from utils.scheduler_utils import SchedulerUtils


class GreedyScheduler:

    def __init__(self, instance_data: InstanceData):
        self.instance_data = instance_data

    def generate_solution(self) -> Solution:
        time = self.instance_data.opening_time

        total_score = 0
        solution = []

        while time <= self.instance_data.closing_time:
            valid_channel_indexes = SchedulerUtils.get_valid_schedules(scheduled_programs=solution,
                                                                       instance_data=self.instance_data,
                                                                       schedule_time=time)
            if not valid_channel_indexes:
                time += 1
                continue

            best_channel, channel_program, fitness = AlgorithmUtils.get_best_fit(scheduled_programs=solution,
                                                                                 instance_data=self.instance_data,
                                                                                 schedule_time=time,
                                                                                 valid_channel_indexes=valid_channel_indexes)

            if fitness <= 0 or (solution and solution[-1].channel_id == best_channel.channel_id):
                time += 1
                continue

            schedule = Schedule(program_id=channel_program.program_id, channel_id=best_channel.channel_id,
                                start=channel_program.start, end=channel_program.end, fitness=fitness,
                                unique_program_id=channel_program.unique_id)

            if solution and solution[-1].start <= schedule.start < solution[-1].end:
                solution[-1].end = schedule.start

            solution.append(schedule)
            time += self.instance_data.min_duration
            total_score += fitness

        return Solution(scheduled_programs=solution, total_score=total_score)
