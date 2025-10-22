# scheduler/beam_search.py
from typing import Tuple, List, Optional, Dict
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
import copy


class BeamSearchScheduler:
    """
    Beam Search scheduler with:
      - minute-level skip_table (hash table) for fast jumps (value = minutes to shift, capped at 30)
      - beam search expansion (beam_width)
      - fallback: if all immediate fitness <= 0, still pick the best candidate to fill schedule
      - small bounded backtrack on the last window to try to improve overall score
      - caches program lookups per channel/time for O(1) access
    """

    def __init__(self, instance_data: InstanceData, beam_width: int = 3, validate_constraints: bool = True,
                 jump_cap: int = 30, backtrack_window: int = 4):
        self.instance_data = instance_data
        self.beam_width = max(1, beam_width)
        self.validate_constraints = validate_constraints
        self.jump_cap = max(1, jump_cap)            # cap of minutes to jump when skipping
        self.backtrack_window = max(0, backtrack_window)

        # build sorted interesting times and per-minute skip_table (hash table)
        self.interesting_times = self._build_interesting_times()
        self.skip_table: Dict[int, int] = self._build_skip_table()

        # cache for channel/time -> program lookup to avoid repeated scanning
        self._channel_time_cache: Dict[Tuple[int, int], object] = {}

        # deterministic tie-breaking seed (optional)
        random.seed(0)

    # ---------------- public ----------------

    def generate_solution(self) -> Solution:
        schedules, total_score = self._beam_search()
        # apply bounded backtrack to try to improve score modestly
        if self.backtrack_window > 0 and schedules:
            schedules, total_score = self._backtrack_improve(schedules, total_score, window=self.backtrack_window)
        return Solution(scheduled_programs=schedules, total_score=int(total_score))

    # ---------------- core beam search ----------------

    def _beam_search(self) -> Tuple[List[Schedule], int]:
        start_time = self.instance_data.opening_time
        closing_time = self.instance_data.closing_time

        # Beam is list of (score, time, partial_schedule)
        beam: List[Tuple[float, int, List[Schedule]]] = [(0.0, start_time, [])]

        best_solution: List[Schedule] = []
        best_score: float = float('-inf')

        while beam:
            candidates: List[Tuple[float, int, List[Schedule]]] = []

            for current_score, current_time, current_solution in beam:
                # if candidate reached end, update best and skip expansion
                if current_time >= closing_time:
                    if current_score > best_score:
                        best_score = current_score
                        best_solution = current_solution
                    continue

                # get valid channels (indices)
                if self.validate_constraints:
                    valid_channels = SchedulerUtils.get_valid_schedules(
                        scheduled_programs=current_solution,
                        instance_data=self.instance_data,
                        schedule_time=current_time
                    )
                else:
                    valid_channels = [
                        i for i, ch in enumerate(self.instance_data.channels)
                        if self._get_channel_program_by_time(ch, current_time) is not None
                    ]

                # if none, jump using skip_table
                if not valid_channels:
                    shift = self.skip_table.get(current_time, self.jump_cap)
                    next_time = min(current_time + shift, closing_time)
                    candidates.append((current_score, next_time, current_solution))
                    continue

                # expand each valid channel
                expanded = []
                for ch_idx in valid_channels:
                    channel = self.instance_data.channels[ch_idx]
                    program = self._get_channel_program_by_time(channel, current_time)
                    if program is None:
                        continue

                    # skip obvious overlap / duplicates
                    if current_solution:
                        last = current_solution[-1]
                        if last.unique_program_id == program.unique_id or program.start < last.end:
                            continue

                    # immediate fitness (contribution)
                    fitness = (
                        getattr(program, "score", 0)
                        + AlgorithmUtils.get_time_preference_bonus(self.instance_data, program, current_time)
                        + AlgorithmUtils.get_switch_penalty(current_solution, self.instance_data, channel)
                        + AlgorithmUtils.get_delay_penalty(current_solution, self.instance_data, program, current_time)
                        + AlgorithmUtils.get_early_termination_penalty(current_solution, self.instance_data, program, current_time)
                    )

                    # allow non-positive fitness but save value — we'll still consider the best among them
                    sched = ScheduleModel(
                        program_id=program.program_id,
                        channel_id=channel.channel_id,
                        start=program.start,
                        end=program.end,
                        fitness=int(fitness),
                        unique_program_id=program.unique_id
                    )

                    new_solution = current_solution + [sched]
                    new_score = current_score + fitness
                    expanded.append((new_score, program.end, new_solution))

                # If no expansion due to checks, we should still jump forward
                if not expanded:
                    shift = self.skip_table.get(current_time, self.jump_cap)
                    next_time = min(current_time + shift, closing_time)
                    candidates.append((current_score, next_time, current_solution))
                else:
                    # If all fitnesses are non-positive, we still want to pick the best among them
                    # expanded already contains them; append to candidates
                    candidates.extend(expanded)

            if not candidates:
                break

            # reduce to top beam_width by score
            beam = heapq.nlargest(self.beam_width, candidates, key=lambda x: x[0])

            # update best if any reached end
            for score, time, sol in beam:
                if time >= closing_time and score > best_score:
                    best_score = score
                    best_solution = sol

        if best_score == float('-inf'):
            return [], 0
        # ensure integer score
        return best_solution, int(best_score)

    # ---------------- helpers ----------------

    def _build_interesting_times(self) -> List[int]:
        times = set()
        for ch in getattr(self.instance_data, "channels", []):
            for p in getattr(ch, "programs", []):
                if getattr(p, "start", None) is not None:
                    times.add(p.start)
                if getattr(p, "end", None) is not None:
                    times.add(p.end)
        cleaned = [t for t in times if t is not None and self.instance_data.opening_time <= t <= self.instance_data.closing_time]
        cleaned.sort()
        return cleaned

    def _build_skip_table(self) -> Dict[int, int]:
        """
        Build per-minute skip table (hash map).
        For each minute 'm' in [opening_time, closing_time):
          - find next interesting time > m
          - compute shift = min(next_interesting - m, jump_cap)
          - if no next interesting, set shift = jump_cap (or closing_time - m if smaller)
        This allows O(1) skip decisions at runtime.
        """
        opening = self.instance_data.opening_time
        closing = self.instance_data.closing_time
        arr = self.interesting_times
        skip = {}

        # for faster bisect, use arr directly
        for m in range(opening, closing):
            if not arr:
                skip[m] = min(self.jump_cap, closing - m)
                continue
            idx = bisect.bisect_right(arr, m)
            if idx >= len(arr):
                skip[m] = min(self.jump_cap, closing - m)
            else:
                next_t = arr[idx]
                delta = next_t - m
                skip[m] = delta if delta <= self.jump_cap else self.jump_cap
        return skip

    def _get_channel_program_by_time_cached(self, channel_idx: int, time: int):
        return self._get_channel_program_by_time(self.instance_data.channels[channel_idx], time)

    def _get_channel_program_by_time(self, channel, time: int):
        """
        Cache channel/time -> program lookup.
        Assumes Utils.get_channel_program_by_time(channel, time) exists and returns the program or None.
        """
        key = (getattr(channel, "channel_id", id(channel)), int(time))
        if key in self._channel_time_cache:
            return self._channel_time_cache[key]
        p = Utils.get_channel_program_by_time(channel, time)
        self._channel_time_cache[key] = p
        return p

    def _score_full_schedule(self, scheduled: List[Schedule]) -> int:
        s = 0.0
        for idx, sch in enumerate(scheduled):
            ch = next((c for c in self.instance_data.channels if c.channel_id == sch.channel_id), None)
            if not ch:
                continue
            prog = next((p for p in ch.programs if p.unique_id == sch.unique_program_id), None)
            if not prog:
                continue
            prefix = scheduled[:idx]
            s += (
                getattr(prog, "score", 0)
                + AlgorithmUtils.get_time_preference_bonus(self.instance_data, prog, prog.start)
                + AlgorithmUtils.get_switch_penalty(prefix, self.instance_data, ch)
                + AlgorithmUtils.get_delay_penalty(prefix, self.instance_data, prog, prog.start)
                + AlgorithmUtils.get_early_termination_penalty(prefix, self.instance_data, prog, prog.start)
            )
        return int(s)

    def _backtrack_improve(self, scheduled: List[Schedule], total_score: int, window: int = 4) -> Tuple[List[Schedule], int]:
        """
        Try to improve the last `window` scheduled items by re-generating alternatives.
        - Remove last `k` items, then greedily refill that window with the best possible sequence.
        - Keep the modification only if it improves total schedule score.
        This is a small bounded backtrack — cheap and usually improves local quality.
        """
        n = len(scheduled)
        if n == 0 or window <= 0:
            return scheduled, total_score

        window = min(window, n)
        prefix = scheduled[: n - window]
        prefix_score = self._score_full_schedule(prefix)

        # compute start time where we need to refill
        refill_time = prefix[-1].end if prefix else self.instance_data.opening_time

        # greedily build best window replacement (try top candidates at each step)
        candidate_solutions = []

        # We'll explore up to beam_width options at each step in the window (bounded tree)
        nodes = [ (prefix_score, refill_time, prefix) ]  # tuples of (score_so_far, cur_time, sol_list)
        max_depth = window

        for depth in range(max_depth):
            next_nodes = []
            for cur_score, cur_time, cur_sol in nodes:
                if cur_time >= self.instance_data.closing_time:
                    next_nodes.append((cur_score, cur_time, cur_sol))
                    continue

                valid_channels = SchedulerUtils.get_valid_schedules(
                    scheduled_programs=cur_sol,
                    instance_data=self.instance_data,
                    schedule_time=cur_time
                )
                if not valid_channels:
                    shift = self.skip_table.get(cur_time, self.jump_cap)
                    next_time = min(cur_time + shift, self.instance_data.closing_time)
                    next_nodes.append((cur_score, next_time, cur_sol))
                    continue

                expansions = []
                for ch_idx in valid_channels:
                    ch = self.instance_data.channels[ch_idx]
                    prog = self._get_channel_program_by_time(ch, cur_time)
                    if not prog:
                        continue
                    if cur_sol and (cur_sol[-1].unique_program_id == prog.unique_id or prog.start < cur_sol[-1].end):
                        continue

                    fitness = (
                        getattr(prog, "score", 0)
                        + AlgorithmUtils.get_time_preference_bonus(self.instance_data, prog, cur_time)
                        + AlgorithmUtils.get_switch_penalty(cur_sol, self.instance_data, ch)
                        + AlgorithmUtils.get_delay_penalty(cur_sol, self.instance_data, prog, cur_time)
                        + AlgorithmUtils.get_early_termination_penalty(cur_sol, self.instance_data, prog, cur_time)
                    )
                    sched = ScheduleModel(program_id=prog.program_id, channel_id=ch.channel_id,
                                          start=prog.start, end=prog.end, fitness=int(fitness),
                                          unique_program_id=prog.unique_id)
                    new_sol = cur_sol + [sched]
                    new_score = cur_score + fitness
                    expansions.append((new_score, prog.end, new_sol))

                if not expansions:
                    shift = self.skip_table.get(cur_time, self.jump_cap)
                    next_time = min(cur_time + shift, self.instance_data.closing_time)
                    next_nodes.append((cur_score, next_time, cur_sol))
                else:

                    expansions.sort(key=lambda x: x[0], reverse=True)
                    for ex in expansions[: self.beam_width]:
                        next_nodes.append(ex)

            nodes = next_nodes

        best_node = max(nodes, key=lambda x: x[0]) if nodes else (prefix_score, refill_time, prefix)
        new_prefix_score, _, new_prefix = best_node
        tail = scheduled[n:]  # normally empty; kept for safety
        new_schedule = new_prefix + tail
        new_total = self._score_full_schedule(new_schedule)

        if new_total > total_score:
            return new_schedule, new_total
        return scheduled, total_score
