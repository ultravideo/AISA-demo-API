* clone the Kvazaar repository and build and install Kvazaar according to the instructions in Kvazaar repository. https://github.com/ultravideo/kvazaar
* create and activate virtual env `python -m venv venv && source /venv/bin/activate`
* install requirements `pip install -r requirements.txt`
* install redis and start `redis-server`
* start `rq worker`
* start server `flask --app src run`
* run `python read_and_feed.py` is used to divide the input video into 10 second segments. Currently, the time stamping 
starts from zero instead of the real time stamp.
* `python test.py` for simple testing