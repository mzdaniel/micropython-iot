import time
import asyncio
import thingflow.filters.output  # This has output side-effect on OutputThing
import thingflow.filters.json
from thingflow.base import (Scheduler, OutputThing, SensorAsOutputThing,
    InputThing, from_list, FatalError)
from thingflow.adapters.mqtt import MQTTReader, MQTTWriter
from collections import namedtuple
from cpx_driver import CPX, vumeter

StripEvent = namedtuple('StripEvent', ['strip_id', 'ts', 'val'])

strip_data = list(range(256))
cpx = CPX('/dev/ttyACM0')


class LightSensor(SensorAsOutputThing):
    '''Create a Circuit Playground LightSensor'''
    def __init__(self, sensor_id='lux-1'):
        '''Initialization can fail as it is dependent on hardware'''
        super().__init__(self)
        self.sensor_id = sensor_id  # Required by SensorAsOutputThing
    def sample(self):
        return cpx.light


class StripInputThing(InputThing):
    def on_next(self, evt):
        ''' Display on neopixels the 0 <= level <= 255 transformation to a
            pretty intensity colorwheel (ore pixels light-up varying in
            intensity and turning from red to blue.
        '''
        level = evt.val
        cpx.neopixel(buf=vumeter(level))


class StripOutputThing(OutputThing):
    def __init__(self):
        super().__init__()
        self.iter = iter(strip_data)
    def _observe(self):
        'Send a normalize 0 <= value <= 255'
        try:
            level = next(self.iter)
            event = StripEvent(strip_id='strip-1', ts=time.time(), val=level)
            self._dispatch_next(event)
        except StopIteration:
            pass   #self._dispatch_completed()
        except FatalError:
            raise
        except Exception as e:
            self._dispatch_error(e)


sched = Scheduler(asyncio.get_event_loop())


# Sensor data flow to mqtt
sensor = LightSensor()
mqtt_sensor = MQTTWriter('localhost', topics=[('sensor-data', 0)])
sensor.output().to_json().connect(mqtt_sensor)
sched.schedule_periodic(sensor, 1.0)

# Strip data flow to mqtt
strip_ctr = StripOutputThing()
mqtt_trip = MQTTWriter('localhost', topics=[('strip-data', 0)])
strip_ctr.output().to_json().connect(mqtt_trip)
sched.schedule_periodic(strip_ctr, 0.1)

# Take the strip data flow from mqtt and send it to the strip
strip = StripInputThing()
mqtt_reader = MQTTReader('localhost', topics=[('strip-data', 0)])
mqtt_reader.map(lambda msg: msg.payload.decode())\
    .from_json(constructor=StripEvent).output().connect(strip)
sched.schedule_on_private_event_loop(mqtt_reader)


sched.run_forever()
