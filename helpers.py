import os

def remaining_space(directory):
    disk = os.statvfs(directory)

    totalBytes = float(disk.f_bsize*disk.f_blocks)
    totalUsedSpace = float(disk.f_bsize*(disk.f_blocks-disk.f_bfree))
    totalAvailSpace = float(disk.f_bsize*disk.f_bfree)
    totalAvailSpaceNonRoot = float(disk.f_bsize*disk.f_bavail)

    print("available space for non-super user: %d Bytes = %.2f KBytes = %.2f MBytes = %.2f GBytes " % (totalAvailSpaceNonRoot, totalAvailSpaceNonRoot/1024, totalAvailSpaceNonRoot/1024/1024, totalAvailSpaceNonRoot/1024/1024/1024))
    return disk.f_frsize * disk.f_bavail
