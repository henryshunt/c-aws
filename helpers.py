import os

def remaining_space(directory):
    """ Returns the amount of remaining space in gigabytes, for non-root users,
        for the specified directory to a device
    """
    disk = os.statvfs(directory)
    non_root_space = float(disk.f_bsize * disk.f_bavail)
    return non_root_space / 1024 / 1024 / 1024
