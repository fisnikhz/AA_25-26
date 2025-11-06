# scheduler/beam_search.py
from typing import Tuple, List, Optional, Dict, Iterable
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
    SEG_CAP = 4

    def __init__(self,
                 instance_data: InstanceData,
                 beam_width: int = 3,
                 validate_constraints: bool = True,
                 jump_cap: int = 30,
                 backtrack_window: int = 4):
        self.instance_data = instance_data
        self.beam_width = max(1, beam_width)
        self.validate_constraints = validate_constraints
        self.jump_cap = max(1, jump_cap)
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

                # no channel fits -> jump
                if not valid_channels:
                    shift = self.skip_table.get(current_time, self.jump_cap)
                    next_time = min(current_time + shift, closing_time)
                    candidates.append((current_score, next_time, current_solution))
                    continue

                expanded_any = False

                for ch_idx in valid_channels:
                    ch = self.instance_data.channels[ch_idx]
                    prog = self._get_channel_program_by_time(ch, current_time)
                    if prog is None:
                        continue

                    # avoid immediate duplicate of the exact same unique program back-to-back
                    if current_solution:
                        last = current_solution[-1]
                        if last.unique_program_id == getattr(prog, "unique_id", None):
                            # still allow if we will continue later with a non-overlapping segment
                            if current_time < last.end:
                                continue

                    # enumerate segment options (late start / early stop / full)
                    for seg_start, seg_end in self._segment_options(current_time, prog):
                        # sanity: monotonic and min duration
                        if not (seg_start < seg_end):
                            continue

                        # schedule model for this segment
                        sched = ScheduleModel(
                            program_id=prog.program_id,
                            channel_id=ch.channel_id,
                            start=seg_start,
                            end=seg_end,
                            fitness=0,  # temporary; we compute below
                            unique_program_id=prog.unique_id
                        )

                        if current_solution and seg_start < current_solution[-1].end:
                            continue

                        vprog = self._virtual_program(prog, seg_start, seg_end)
                        fitness = (
                                getattr(prog, "score", 0)
                                + AlgorithmUtils.get_time_preference_bonus(self.instance_data, vprog, seg_start)
                                + AlgorithmUtils.get_switch_penalty(current_solution, self.instance_data, ch)
                                + AlgorithmUtils.get_delay_penalty(current_solution, self.instance_data, vprog,
                                                                   seg_start)
                                + AlgorithmUtils.get_early_termination_penalty(current_solution, self.instance_data,
                                                                               vprog, seg_start)
                        )
                        sched.fitness = int(fitness)

                        new_solution = current_solution + [sched]
                        new_score = current_score + fitness
                        candidates.append((new_score, seg_end, new_solution))
                        expanded_any = True

                if not expanded_any:
                    # still move time forward
                    shift = self.skip_table.get(current_time, self.jump_cap)
                    next_time = min(current_time + shift, closing_time)
                    candidates.append((current_score, next_time, current_solution))

            if not candidates:
                break

            beam = heapq.nlargest(self.beam_width, candidates, key=lambda x: x[0])

            # update best
            for score, time, sol in beam:
                if time >= closing_time and score > best_score:
                    best_score = score
                    best_solution = sol

        if best_score == float('-inf'):
            return [], 0
        return best_solution, int(best_score)

    # ---------------- segment generation ----------------

    def _segment_options(self, current_time: int, prog) -> Iterable[Tuple[int, int]]:
        O = self.instance_data.opening_time
        E = self.instance_data.closing_time
        D = getattr(self.instance_data, "min_duration", 1)

        # late start = start at the later of current_time or program.start
        seg_start = max(current_time, prog.start, O)
        if seg_start >= prog.end or seg_start >= E:
            return []

        ends = set()
        ends.add(min(prog.end, E))

        # next interesting time after (seg_start + D)
        idx = bisect.bisect_left(self.interesting_times, seg_start + D)
        for j in range(idx, min(idx + 6, len(self.interesting_times))):
            t = self.interesting_times[j]
            if seg_start + D <= t <= prog.end and t <= E:
                ends.add(t)

        min_ok_end = seg_start + D
        if min_ok_end <= prog.end and min_ok_end <= E:
            ends.add(min_ok_end)

        ends_list = sorted(ends)
        chosen: List[int] = []

        full_end = min(prog.end, E)
        if full_end in ends_list:
            chosen.append(full_end)

        if ends_list and ends_list[0] != full_end:
            chosen.append(ends_list[0])

        if len(ends_list) >= 3:
            chosen.append(ends_list[len(ends_list) // 2])

        if min_ok_end not in chosen and min_ok_end in ends_list:
            chosen.append(min_ok_end)

        chosen = chosen[:self.SEG_CAP]

        return [(seg_start, e) for e in chosen if e - seg_start >= D]

    # ---------------- helpers ----------------

    def _virtual_program(self, prog, new_start: int, new_end: int):

        class V:
            pass

        v = V()
        v.program_id = prog.program_id
        v.unique_id = getattr(prog, "unique_id", getattr(prog, "program_id", None))
        v.start = new_start
        v.end = new_end
        v.genre = prog.genre
        v.score = prog.score
        v.channel_id = getattr(prog, "channel_id", None)
        return v

    def _build_interesting_times(self) -> List[int]:
        times = set()
        for ch in getattr(self.instance_data, "channels", []):
            for p in getattr(ch, "programs", []):
                if getattr(p, "start", None) is not None:
                    times.add(p.start)
                if getattr(p, "end", None) is not None:
                    times.add(p.end)

        # Priority block boundaries
        for blk in getattr(self.instance_data, "priority_blocks", []):
            times.add(blk.start)
            times.add(blk.end)

        # Time preference boundaries
        for pref in getattr(self.instance_data, "time_preferences", []):
            times.add(pref.start)
            times.add(pref.end)

        O = self.instance_data.opening_time
        E = self.instance_data.closing_time
        cleaned = [t for t in times if t is not None and O <= t <= E]
        cleaned.sort()
        return cleaned

    def _build_skip_table(self) -> Dict[int, int]:
   #hash table function
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

    def _get_channel_program_by_time(self, channel, time: int):
       #Cache channel/time -> program lookup.
        #Assumes Utils.get_channel_program_by_time(channel, time) exists and returns the program or None.
        key = (getattr(channel, "channel_id", id(channel)), int(time))
        if not hasattr(self, "_channel_time_cache"):
            self._channel_time_cache = {}
        if key in self._channel_time_cache:
            return self._channel_time_cache[key]
        p = Utils.get_channel_program_by_time(channel, time)
        self._channel_time_cache[key] = p
        return p

    def _score_full_schedule(self, scheduled: List[Schedule]) -> int:
        total = 0.0
        prefix: List[Schedule] = []
        for sch in scheduled:
            ch = next((c for c in self.instance_data.channels if c.channel_id == sch.channel_id), None)
            if not ch:
                prefix.append(sch)
                continue
            prog = next((p for p in ch.programs if getattr(p, "unique_id", None) == sch.unique_program_id), None)
            if not prog:
                prog = next((p for p in ch.programs if p.program_id == sch.program_id), None)
            if not prog:
                prefix.append(sch)
                continue

            vprog = self._virtual_program(prog, sch.start, sch.end)

            total += (
                    getattr(prog, "score", 0)
                    + AlgorithmUtils.get_time_preference_bonus(self.instance_data, vprog, sch.start)
                    + AlgorithmUtils.get_switch_penalty(prefix, self.instance_data, ch)
                    + AlgorithmUtils.get_delay_penalty(prefix, self.instance_data, vprog, sch.start)
                    + AlgorithmUtils.get_early_termination_penalty(prefix, self.instance_data, vprog, sch.start)
            )
            prefix.append(sch)
        return int(total)

    def _backtrack_improve(self, scheduled: List[Schedule], total_score: int, window: int = 4) -> Tuple[
        List[Schedule], int]:
        n = len(scheduled)
        if n == 0 or window <= 0:
            return scheduled, total_score

        window = min(window, n)
        prefix = scheduled[: n - window]
        prefix_score = self._score_full_schedule(prefix)

        # compute start time where we need to refill
        refill_time = prefix[-1].end if prefix else self.instance_data.opening_time

        nodes: List[Tuple[float, int, List[Schedule]]] = [(prefix_score, refill_time, prefix)]
        max_depth = window

        for _ in range(max_depth):
            next_nodes: List[Tuple[float, int, List[Schedule]]] = []
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
                    next_nodes.append((cur_score, min(cur_time + shift, self.instance_data.closing_time), cur_sol))
                    continue

                expansions: List[Tuple[float, int, List[Schedule]]] = []
                for ch_idx in valid_channels:
                    ch = self.instance_data.channels[ch_idx]
                    prog = self._get_channel_program_by_time(ch, cur_time)
                    if not prog:
                        continue

                    for seg_start, seg_end in self._segment_options(cur_time, prog):
                        if cur_sol and seg_start < cur_sol[-1].end:
                            continue

                        vprog = self._virtual_program(prog, seg_start, seg_end)
                        fitness = (
                                getattr(prog, "score", 0)
                                + AlgorithmUtils.get_time_preference_bonus(self.instance_data, vprog, seg_start)
                                + AlgorithmUtils.get_switch_penalty(cur_sol, self.instance_data, ch)
                                + AlgorithmUtils.get_delay_penalty(cur_sol, self.instance_data, vprog, seg_start)
                                + AlgorithmUtils.get_early_termination_penalty(cur_sol, self.instance_data, vprog,
                                                                               seg_start)
                        )
                        sched = ScheduleModel(program_id=prog.program_id, channel_id=ch.channel_id,
                                              start=seg_start, end=seg_end, fitness=int(fitness),
                                              unique_program_id=prog.unique_id)
                        new_sol = cur_sol + [sched]
                        expansions.append((cur_score + fitness, seg_end, new_sol))

                if expansions:
                    expansions.sort(key=lambda x: x[0], reverse=True)
                    next_nodes.extend(expansions[: self.beam_width])
                else:
                    shift = self.skip_table.get(cur_time, self.jump_cap)
                    next_nodes.append((cur_score, min(cur_time + shift, self.instance_data.closing_time), cur_sol))

            nodes = next_nodes

        best_node = max(nodes, key=lambda x: x[0]) if nodes else (prefix_score, refill_time, prefix)
        new_total = self._score_full_schedule(best_node[2])

        if new_total > total_score:
            return best_node[2], new_total
        return scheduled, total_score