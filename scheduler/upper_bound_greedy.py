import copy
from typing import Optional

from scheduler.greedy_scheduler import GreedyScheduler

_MIN_ATTRS = ("min_duration", "minDur", "min_time", "duration_min")
_BONUS_MIN_ATTRS = ("bonus_min_duration", "bonusMin", "min_for_bonus")

class UpperBoundGreedy:
    """
    Upper bound via normalization:
      - For every program, force end = start + required_min
      - required_min = max(global_min, per-program min, bonus-min if enabled)
      - Then run the existing GreedyScheduler on this minimized instance.
    """

    def __init__(self, instance, honor_bonus_min: bool = True):
        self.instance = instance
        self.honor_bonus_min = honor_bonus_min

    @staticmethod
    def _first_attr(obj, names):
        for n in names:
            if hasattr(obj, n):
                v = getattr(obj, n)
                if v is not None:
                    return v
        return None

    def _required_min(self, program) -> int:
        # global min from InstanceData (used in your Greedy check)
        gmin = getattr(self.instance, "min_duration", 0) or 0

        pmin = self._first_attr(program, _MIN_ATTRS)
        if pmin is None:
            # fall back to current length if no per-program min
            pmin = max(0, getattr(program, "end", 0) - getattr(program, "start", 0))

        req = max(int(gmin), int(pmin))

        if self.honor_bonus_min:
            bmin = self._first_attr(program, _BONUS_MIN_ATTRS)
            if bmin is not None:
                req = max(req, int(bmin))

        # never below 1 minute
        return max(1, req)

    def _normalize_instance(self, inst_copy):
        for ch in inst_copy.channels:
            for p in ch.programs:
                # keep start as-is; force minimal legal length
                start = getattr(p, "start", None)
                end = getattr(p, "end", None)
                if start is None or end is None:
                    # if your Parser sometimes only sets duration, derive end from start
                    start = start or 0
                    duration = getattr(p, "duration", self._required_min(p))
                    end = start + int(duration)

                dur = self._required_min(p)

                # force the program length to the required minimum
                p.start = int(start)
                p.end = int(start) + int(dur)

                # keep any auxiliary fields in sync if they exist
                if hasattr(p, "duration"):
                    p.duration = int(dur)
                if hasattr(p, "min_duration"):
                    p.min_duration = int(dur)
                if hasattr(p, "max_duration") and getattr(p, "max_duration") is not None:
                    # cap max = min so Greedy/validators treat it fixed-length
                    p.max_duration = int(dur)

    def generate_solution(self):
        inst_copy = copy.deepcopy(self.instance)
        self._normalize_instance(inst_copy)

        # Now run existing Greedy over the minimized instance
        gs = GreedyScheduler(inst_copy)
        return gs.generate_solution()
