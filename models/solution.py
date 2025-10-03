from typing import List

from models.schedule import Schedule


class Solution:
    def __init__(self, schedule_plan: List[Schedule], total_score: int):
        self.schedule_plan = schedule_plan
        self.total_score = total_score

    def __repr__(self):
        return f"Solution({self.total_score}, schedule_plan: {self.schedule_plan})"