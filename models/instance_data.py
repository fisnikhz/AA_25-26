class InstanceData:
    def __init__(self, opening_time, closing_time, min_duration, max_consecutive_genre,
                 channels_count, switch_penalty, termination_penalty,
                 priority_blocks, time_preferences, channels):
        self.opening_time = opening_time
        self.closing_time = closing_time
        self.min_duration = min_duration
        self.max_consecutive_genre = max_consecutive_genre
        self.channels_count = channels_count
        self.switch_penalty = switch_penalty
        self.termination_penalty = termination_penalty
        self.priority_blocks = priority_blocks
        self.time_preferences = time_preferences
        self.channels = channels

    def __repr__(self):
        return f"InstanceData({self.channels_count} channels, {len(self.time_preferences)} time prefs)"
