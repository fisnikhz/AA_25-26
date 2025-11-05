import copy
from typing import Optional, Sequence
from scheduler.greedy_scheduler import GreedyScheduler

_MIN_ATTRS = ("min_duration", "minDur", "min_time", "duration_min")
_BONUS_MIN_ATTRS = ("bonus_min_duration", "bonusMin", "min_for_bonus")

class UpperBoundGreedyRelaxed:
    def __init__(self, instance,
                 relax_constraint: Optional[str] = "time_pref",   
                 honor_bonus_min: bool = True,
                 preference_slack: int = 15,                     
                 shift_candidates: Sequence[int] = (0, 5, -5, 10, -10)):
        self.instance = instance
        self.relax_constraint = relax_constraint
        self.honor_bonus_min = honor_bonus_min
        self.preference_slack = preference_slack
        self.shift_candidates = shift_candidates

    @staticmethod
    def _first_attr(obj, names):
        for n in names:
            if hasattr(obj, n):
                v = getattr(obj, n)
                if v is not None:
                    return v
        return None

    def _required_min(self, program) -> int:
        gmin = getattr(self.instance, "min_duration", 0) or 0
        pmin = self._first_attr(program, _MIN_ATTRS)
        if pmin is None:
            pmin = max(0, getattr(program, "end", 0) - getattr(program, "start", 0))
        req = max(int(gmin), int(pmin))
        if self.honor_bonus_min:
            bmin = self._first_attr(program, _BONUS_MIN_ATTRS)
            if bmin is not None:
                req = max(req, int(bmin))
        return max(1, req)

    def _normalize_min(self, inst_copy):
        for ch in inst_copy.channels:
            for p in ch.programs:
                start = getattr(p, "start", 0)
                dur = self._required_min(p)
                p.start = int(start)
                p.end = int(start) + int(dur)
                if hasattr(p, "duration"): p.duration = int(dur)
                if hasattr(p, "min_duration"): p.min_duration = int(dur)
                if hasattr(p, "max_duration") and getattr(p, "max_duration") is not None:
                    p.max_duration = int(dur)

    def _apply_relax_flags(self, inst_copy):
        setattr(inst_copy, "relax_constraint", self.relax_constraint)
        setattr(inst_copy, "preference_slack", self.preference_slack)

    def _try_shifts(self, inst_copy):
        best_sol = None
        best_score = -10**18
        original = copy.deepcopy(inst_copy)

        for delta in self.shift_candidates:
            variant = copy.deepcopy(original)
            for ch in variant.channels:
                for p in ch.programs:
                    p.start += delta
                    p.end += delta
                    p.start = max(p.start, variant.opening_time)
                    p.end   = min(p.end,   variant.closing_time)
                    if p.end - p.start < self._required_min(p):
                        p.end = p.start + self._required_min(p)
                        if p.end > variant.closing_time:
                            pass

            sol = GreedyScheduler(variant).generate_solution()
            if sol.total_score > best_score:
                best_score, best_sol = sol.total_score, sol

        return best_sol

    def generate_solution(self):
        inst_copy = copy.deepcopy(self.instance)
        self._normalize_min(inst_copy)      
        self._apply_relax_flags(inst_copy)

        sol = self._try_shifts(inst_copy)
        return sol
