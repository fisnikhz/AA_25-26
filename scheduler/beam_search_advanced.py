from typing import Tuple, List, Dict
from models.instance_data import InstanceData
from models.schedule import Schedule
from models.solution import Solution
from utils.scheduler_utils import SchedulerUtils
from utils.utils import Utils
from utils.algorithm_utils import AlgorithmUtils
from models.schedule import Schedule as ScheduleModel
import bisect
import heapq
import random


class BeamSearchSchedulerAdvanced:
    def __init__(self, instance_data: InstanceData,
                 beam_width: int = 3,
                 validate_constraints: bool = True,
                 jump_cap: int = 30,
                 backtrack_window: int = 10,
                 restarts: int = 3):

        self.instance_data = instance_data
        self.beam_width = max(1, beam_width)
        self.validate_constraints = validate_constraints
        self.jump_cap = max(1, jump_cap)
        self.backtrack_window = max(1, backtrack_window)
        self.restarts = max(1, restarts)

        self.interesting_times = self._build_interesting_times()
        self.skip_table = self._build_skip_table()
        self._cache: Dict[Tuple[int, int], object] = {}
        random.seed(0)

    def generate_solution(self) -> Solution:
        best_solution, best_score = [], float('-inf')

        for restart in range(1, self.restarts + 1):
            seed = random.randint(1, 999999)
            random.seed(seed)

            adaptive_beam = self._adjust_beam_width(best_score, restart)
            adaptive_jump = self.jump_cap + restart * 5

            print(f"[Restart {restart}/{self.restarts}] Beam width = {adaptive_beam}, Jump cap = {adaptive_jump}, Seed = {seed}")

            schedules, score = self._beam_search_core(
                beam_width=adaptive_beam,
                jump_cap=adaptive_jump
            )

            if score > best_score:
                best_score = score
                best_solution = schedules

            print(f"  → Restart {restart} finished with score: {int(score)}")

        print(f"\nBest solution after {self.restarts} restarts: {int(best_score)}\n")
        return Solution(scheduled_programs=best_solution, total_score=int(best_score))

    def _beam_search_core(self, beam_width: int, jump_cap: int) -> Tuple[List[Schedule], float]:
        best_score = float('-inf')
        best_solution = []
        beam: List[Tuple[float, int, List[Schedule]]] = [(0.0, self.instance_data.opening_time, [])]

        while beam:
            candidates = []
            for score, t, partial in beam:
                if t >= self.instance_data.closing_time:
                    if score > best_score:
                        best_score = score
                        best_solution = partial[:]
                    continue

                channels = list(range(len(self.instance_data.channels)))
                if random.random() < 0.25:
                    random.shuffle(channels)

                valid_channels = SchedulerUtils.get_valid_schedules(
                    scheduled_programs=partial,
                    instance_data=self.instance_data,
                    schedule_time=t
                ) if self.validate_constraints else channels

                if not valid_channels:
                    next_t = min(t + self.skip_table.get(t, jump_cap), self.instance_data.closing_time)
                    candidates.append((score, next_t, partial))
                    continue

                expanded = []
                for ch_idx in valid_channels:
                    ch = self.instance_data.channels[ch_idx]
                    prog = self._get_program(ch, t)
                    if not prog:
                        continue
                    if partial and (partial[-1].unique_program_id == prog.unique_id or prog.start < partial[-1].end):
                        continue

                    fitness = (
                        getattr(prog, "score", 0)
                        + AlgorithmUtils.get_time_preference_bonus(self.instance_data, prog, t)
                        + AlgorithmUtils.get_switch_penalty(partial, self.instance_data, ch)
                        + AlgorithmUtils.get_delay_penalty(partial, self.instance_data, prog, t)
                        + AlgorithmUtils.get_early_termination_penalty(partial, self.instance_data, prog, t)
                    )

                    sched = ScheduleModel(
                        program_id=prog.program_id,
                        channel_id=ch.channel_id,
                        start=prog.start,
                        end=prog.end,
                        fitness=int(fitness),
                        unique_program_id=prog.unique_id
                    )
                    new_sol = partial + [sched]
                    expanded.append((score + fitness, prog.end, new_sol))

                if not expanded:
                    next_t = min(t + self.skip_table.get(t, jump_cap), self.instance_data.closing_time)
                    candidates.append((score, next_t, partial))
                else:
                    candidates.extend(expanded)

            if not candidates:
                break
            beam = heapq.nlargest(beam_width, candidates, key=lambda x: x[0])

        return best_solution, best_score

    def _adjust_beam_width(self, best_score: float, restart: int) -> int:
        if best_score < 0:
            return min(self.beam_width + restart, 8)
        elif restart % 2 == 0:
            return max(2, self.beam_width - 1)
        else:
            return self.beam_width + 1

    def _get_program(self, channel, time: int):
        key = (channel.channel_id, time)
        if key in self._cache:
            return self._cache[key]
        prog = Utils.get_channel_program_by_time(channel, time)
        self._cache[key] = prog
        return prog

    def _build_interesting_times(self) -> List[int]:
        times = set()
        for ch in self.instance_data.channels:
            for p in ch.programs:
                times.add(p.start)
                times.add(p.end)
        return sorted(t for t in times if self.instance_data.opening_time <= t <= self.instance_data.closing_time)

    def _build_skip_table(self) -> Dict[int, int]:
        skip = {}
        times = self._build_interesting_times()
        for t in range(self.instance_data.opening_time, self.instance_data.closing_time):
            idx = bisect.bisect_right(times, t)
            if idx >= len(times):
                skip[t] = min(self.jump_cap, self.instance_data.closing_time - t)
            else:
                next_t = times[idx]
                skip[t] = min(next_t - t, self.jump_cap)
        return skip
