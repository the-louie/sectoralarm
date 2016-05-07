import config
import datetime
import hashlib
import json
import os
import sectoralarm


SECTORSTATUS = sectoralarm.SectorStatus(config)

log = SECTORSTATUS.event_log()
loghash = hashlib.sha256(json.dumps(log)).hexdigest()

now = datetime.datetime.now()

LOGFILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'log_'+now.strftime('%Y%m%d_%H%M%S')+'_'+loghash+'.log')

with open(LOGFILE, 'w') as logfile:
    json.dump(log, logfile, indent=4, separators=(',', ': '))
