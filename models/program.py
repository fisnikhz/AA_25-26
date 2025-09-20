class Program:
    def __init__(self, program_id, start, end, genre, score):
        self.program_id = program_id
        self.start = start
        self.end = end
        self.genre = genre
        self.score = score

    def __repr__(self):
        return f"Program({self.program_id}, {self.start}-{self.end}, {self.genre}, {self.score})"
