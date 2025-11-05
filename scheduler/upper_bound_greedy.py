# scheduler/upper_bound_greedy.py
from scheduler.greedy_scheduler import GreedyScheduler
from models.schedule import Schedule
from models.solution import Solution


class UpperBoundGreedy(GreedyScheduler):
    def __init__(
        self,
        instance_data,
        relax_constraint="time_pref",
        honor_bonus_min=True,
        preference_slack=15,
        shift_candidates=(0, 5, 10, 15),  
    ):
        super().__init__(instance_data)
        self.relax_constraint = relax_constraint
        self.honor_bonus_min = honor_bonus_min
        self.preference_slack = int(preference_slack)
        self.shift_candidates = shift_candidates

        self.switch_w = 0.2
        self.earlylate_w = 0.2

    def compute_upper_bound(self) -> float:
        total = sum(p.score for ch in self.instance_data.channels for p in ch.programs)
        total += sum(pref.bonus for pref in self.instance_data.time_preferences)
        return float(total)

    @staticmethod
    def _overlap(a_start, a_end, b_start, b_end) -> bool:
        return max(a_start, b_start) < min(a_end, b_end)

    def get_relaxed_bonus(self, program, start, end) -> float:
        total_bonus = 0.0
        for pref in self.instance_data.time_preferences:
            if pref.preferred_genre.lower() != program.genre.lower():
                continue
            p_start = pref.start - self.preference_slack
            p_end = pref.end + self.preference_slack
            if self._overlap(start, end, p_start, p_end):
                total_bonus += pref.bonus
        return total_bonus

    def relaxed_fitness(self, program, channel, prev_schedule) -> float:
        base_score = program.score
        bonus = self.get_relaxed_bonus(program, program.start, program.end)
        score = base_score + bonus

        if prev_schedule:
            if prev_schedule.channel_id != channel.channel_id:
                score -= self.switch_w * self.instance_data.switch_penalty
            if program.start > prev_schedule.end:
                score -= self.earlylate_w * self.instance_data.termination_penalty

        return max(0.0, score)

    def generate_solution(self) -> Solution:
        print("[INFO] Running Upper-Bound Greedy (continuity-safe)...")

        base_solution = super().generate_solution()
        upper_bound = self.compute_upper_bound()

        relaxed_schedules = []
        total_score = 0.0

        for sch in base_solution.scheduled_programs:
            prog = next(
                (
                    p
                    for ch in self.instance_data.channels
                    for p in ch.programs
                    if p.program_id == sch.program_id
                ),
                None,
            )
            if not prog:
                continue

            best_start, best_end = max(sch.start, prog.start), min(sch.end, prog.end)
            fitness = self.relaxed_fitness(
                program=prog,
                channel=next(
                    (ch for ch in self.instance_data.channels if ch.channel_id == sch.channel_id),
                    None,
                ),
                prev_schedule=relaxed_schedules[-1] if relaxed_schedules else None,
            )

            for shift in self.shift_candidates:
                shifted_start = best_start + shift
                shifted_end = best_end + shift
                if shifted_start < prog.start or shifted_end > prog.end:
                    continue
                bonus = self.get_relaxed_bonus(prog, shifted_start, shifted_end)
                if fitness + 0.5 * bonus > fitness:
                    best_start, best_end, fitness = shifted_start, shifted_end, fitness + 0.5 * bonus

            relaxed_schedules.append(
                Schedule(
                    program_id=prog.program_id,
                    channel_id=sch.channel_id,
                    start=best_start,
                    end=best_end,
                    fitness=fitness,
                    unique_program_id=prog.unique_id,
                )
            )
            total_score += fitness

            if total_score >= 0.95 * upper_bound:
                print("[INFO] Reached 95% of theoretical upper bound — stopping.")
                break

        print(f"[INFO] Final schedule count: {len(relaxed_schedules)} | Score: {total_score:.2f}")
        return Solution(scheduled_programs=relaxed_schedules, total_score=total_score)
