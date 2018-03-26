import os

def remaining_space(directory):
    analysis = os.statvfs(directory)
    return analysis.f_frsize * analysis.f_bavail
