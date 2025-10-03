import json
from pathlib import Path

from models.solution import Solution


class SolutionSerializer:
    """
    Serializer i një liste të schedules (Schedule objects) në JSON.
    """
    def __init__(self, output_file="output.json"):
        self.output_path = Path("data/output/" + output_file)
        # krijo folderin nëse nuk ekziston
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def output_file_name_input():
        output_file_name = str(input("\n Write the output file including extension: "))
        return output_file_name

    def serialize(self, solution: Solution):
        """
        Merr një listë me Schedule objects dhe e ruan si JSON.
        """
        schedules = []
        for schedule in solution.schedule_plan:
            # çdo Schedule kthehet në dict
            schedules.append({
                "channel_id": schedule.channel_id,
                "program_id": schedule.program_id,
                "start_time": schedule.start_time,
                "end_time": schedule.end_time,
                "fitness": schedule.fitness,
                "unique_program_id": schedule.unique_program_id
            })

        data = {
            "total_score": solution.total_score,
            "schedule_plan": schedules
        }

        try:
            with open(self.output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[ERROR] Deshtoi serializimi: {e}")
