import os

def remaining_space(directory):
    """ Returns the amount of remaining space for non-root users in gigabytes
    """
    disk = os.statvfs(directory)
    non_root_space = float(disk.f_bsize * disk.f_bavail)
    return non_root_space / 1024 / 1024 / 1024
