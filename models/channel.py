class Channel:
    def __init__(self, channel_id, programs):
        self.channel_id = channel_id
        self.programs = programs

    def __repr__(self):
        return f"Channel({self.channel_id}, Programs: {len(self.programs)})"
