from ..utils.scheduler_utils import SchedulerUtils
from ..utils.utils import Utils

def schedule_channels(instance):
    time = instance.opening_time
    schedule = []
    while time < instance.closing_time:
        channel = find_best_channel_to_play(schedule, instance, time)
        if channel is not None:
            program = Utils.get_channel_program_by_time(instance.channels[channel], time)
            if program:
                SchedulerUtils.switch_channel(schedule, channel, time, program.end)
                time = program.end
            else:
                time += 1
        else:
            time += 1
    return schedule

def find_best_channel_to_play(schedule, instance, time):
    valid_channels = SchedulerUtils.get_valid_schedules(schedule, instance, time)
    max_score = 0
    best_channel = None
    for channel in valid_channels:
        program = Utils.get_channel_program_by_time(instance.channels[channel], time)
        if program and program.score > max_score:
            max_score = program.score + SchedulerUtils.calculate_bonus_score(program, time)
            best_channel = channel
    return best_channel