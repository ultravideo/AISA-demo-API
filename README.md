* install requirements `pip install -r requirements`
* install redis and start `redis-server`
* start `rq worker`
* start server `flask --app src`
* run `python read_and_feed.py` to generate temp data
* `python test.py` for simple testing