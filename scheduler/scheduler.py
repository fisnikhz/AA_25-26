from ..utils.scheduler_utils import SchedulerUtils
from ..utils.utils import Utils

def schedule_channels(instance):
    time = instance.opening_time
    schedule = []
    while time < instance.closing_time:
        channel, fitness = SchedulerUtils.find_best_channel_to_play(schedule, instance, time)
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