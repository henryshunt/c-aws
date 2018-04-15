import sys
from datetime import datetime
import time
import os

# Wait to allow web response, and only activate when idle
time.sleep(1)

while datetime.utcnow().second < 20:
    time.sleep(0.5)

os.system("shutdown " + sys.argv[1] + " now")
