import json
from pathlib import Path

class SolutionSerializer:
    """
    Serializer i një liste të schedules (Schedule objects) në JSON.
    """
    def __init__(self, output_path="data/output/output.json"):
        self.output_path = Path(output_path)
        # krijo folderin nëse nuk ekziston
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

    def serialize(self, schedules):
        """
        Merr një listë me Schedule objects dhe e ruan si JSON.
        """
        data = []
        for schedule in schedules:
            # çdo Schedule kthehet në dict
            data.append({
                "channel_id": schedule.channel_id,
                "program_id": schedule.program_id,
                "start_time": schedule.start_time,
                "end_time": schedule.end_time,
                "fitness": schedule.fitness,
                "unique_program_id": schedule.unique_program_id
            })

        try:
            with open(self.output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[ERROR] Deshtoi serializimi: {e}")
