"""
qysh ka me shku flow:
    time = opening time
    loop
        zgjedhe kanalin ma mtir per me ja nis loja & llogarite kur o koha me ndrru kanalin
        kqyr a i violate constraint qaj kanal (overlap me constraints)
        nese jo, appendo
        nese po, 
            kqyri kanalet me ren deri sa jo
    ndrro kanalin

d.m.th.: (Ju lutem, argumentet e funksioneve merrni me ni grain of salt mbreta ka mundsi qe ja kom huq)
function schedule_channels(instance):
    time = opening_time
    output = []
    while time <= closing_time
        channel, until = find_best_channel_to_play(time)
        switch_channel(output, channel)
        time = until
    write_to_output_file(output) <-- serializeri

function find_best_channel_to_play(time):
    while true:
        best_channel = max_heap.pop
        if validate(channel, time): <-- validatori
            return channel
            
"""
 def schedule_channels(instance):
    time = instance.opening_time
    output = []
    while time <= instance.closing_time:
        channel, until = find_best_channel_to_play(time)
        switch_channel(output, channel) # <-- qikjo lyp hala pun
        time = until
    write_to_output_file(output)

def find_best_channel_to_play(time):
    """
    Qitu kena me analizu listen e programeve qe jon tu play qitasht, edhe me i rendit qcili ja vlen ma sshumti me play right now edhe me kthy qata qe osht ma i vlefshmi.
    """
    print("The best channel to play is babarecordsTV")

def switch_channel(output, channel)
    output.append(channel
                  """programi"""
                  """fitness, ...""")
