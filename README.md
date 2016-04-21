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
Retrieves the last 30 events in the event log and returns a list with dict. It does some guesswork to convert the dates to sane ones.
```JSON
[
	{
		"timestamp": "2016-02-14 23:17:00",
		"event": "Tillkopplat",
		"user": "Person A"
	}, {
		"timestamp": "2016-02-15 17:09:00",
		"event": "Frånkopplat",
		"user": "Person B"
	}, {
		"timestamp": "2016-02-15 08:31:00",
		"event": "Tillkopplat",
		"user": "Person B"
	}, {
		"timestamp": "2016-02-15 05:40:00",
		"event": "Frånkopplat",
		"user": "Person C"
	}, {
		"timestamp": "2016-02-14 23:23:00",
		"event": "Tillkopplat",
		"user": "Person A"
	}, {
		"timestamp": "2016-02-14 19:24:00",
		"event": "Frånkopplat",
		"user": "Person C"
	}
]
```

### status()
Retrieves the current status, timestamp and name of the person who changed the status.
```JSON
{
	"event": "Tillkopplat",
	"user": "Person A",
	"timestamp": "2016-02-14 23:17:00"
}
```
