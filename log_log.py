import config
import datetime
import hashlib
import json
import sectoralarm

SECTORSTATUS = sectoralarm.SectorStatus(config)
log = SECTORSTATUS.event_log()
loghash = hashlib.sha256(json.dumps(log)).hexdigest()

now = datetime.datetime.now()

with open('./data/log_'+now.strftime('%Y%m%d_%H%M%S')+'_'+loghash+'.log', 'w') as logfile:
    json.dump(log, logfile, indent=4, separators=(',', ': '))
