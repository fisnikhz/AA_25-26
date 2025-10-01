class Schedule:
    """
    Klasa qe perfaqeson nje zgjedhje (nje program i zgjedhur ne nje kanal).
    """

    def __init__(self, channel_id, program_id, start_time, end_time, fitness, unique_program_id):
        self.channel_id = channel_id
        self.program_id = program_id
        self.start_time = start_time
        self.end_time = end_time
        self.fitness = fitness
        self.unique_program_id = unique_program_id

    def to_dict(self):
        """
        Kthen objektin Schedule ne nje dictionary te serializueshem.
        """
        return {
            "channel_id": self.channel_id,
            "program_id": self.program_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "fitness": self.fitness,
            "unique_program_id": self.unique_program_id
        }

    def __repr__(self):
        return (f"Schedule(channel_id={self.channel_id}, program_id={self.program_id}, "
                f"start_time={self.start_time}, end_time={self.end_time}, "
                f"fitness={self.fitness}, unique_program_id={self.unique_program_id})")
