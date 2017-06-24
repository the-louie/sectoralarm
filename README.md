# Sector alarm
Get the current status of your home alarm if you have the Swedish provider Sector Alarm. The two calls are getting the current status and retreiving the log.

## Configuration
You need to supply your login email (username), password and the site-id of the site you want to retrieve information about. Rename the file `config_example.py` to `config.py`.

### Example configuration
```Python
email = 'mylogin@email.com'
password = 'secretpassword'
siteid = '12345678'
```

## Calls

### event_log()
Retrieves all available events in the event log and returns a list with dict.
```JSON
[
	{
		"EventType": "disarmed",
		"LockName": "sitename.event.disarming",
		"User": "user1",
		"Channel": "",
		"Time": "2017-06-18T16:17:00"
	},
	{
		"EventType": "armed",
		"LockName": "sitename.event.arming",
		"User": "user2",
		"Channel": "",
		"Time": "2017-06-17T12:01:00"
	},
	{
		"EventType": "disarmed",
		"LockName": "sitename.event.disarming",
		"User": "user1",
		"Channel": "",
		"Time": "2017-06-17T10:22:00"
	}
]
```

### status()
Retrieves the current status, timestamp and name of the person who changed the status.
```JSON
{
	"ArmedStatus": "disarmed"
}
```
