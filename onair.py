"""
MQTT On air light - Jeremy Blythe
"""
from time import sleep
from enum import Enum
import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO

PIN = 18
MQTT_BROKER = "192.168.86.225"
FLASH_SECONDS = 0.15


class State(Enum):
    """Represents the state of the On Air light"""

    ON = 0
    FLASH = 1
    OFF = 2

    def inc(self):
        """Increment the state, wrap from OFF to ON"""
        if self.value == 2:
            return State(0)
        return State(self.value + 1)


state = State.OFF


def init_gpio(pin):
    """Initialize the pin as an Output. The relay is "Active low", so the pin is set High/True."""
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, True)


def flash(pin):
    """Set the output False then True with a delay so the On Air light recognises it."""
    GPIO.output(pin, False)
    sleep(FLASH_SECONDS)
    GPIO.output(pin, True)
    sleep(FLASH_SECONDS)


def set_state(new_state):
    """
    Increment the state and flash the pin each time until we get to the desired state.
    This allows us to transition to any state. For example ON to OFF requires two flashes
    because we have to go through the FLASHING state.
    """
    # Using a global here for simplicity, would refactor if handling many states
    # pylint: disable=W0603,C0103
    global state
    while state != new_state:
        flash(PIN)
        state = state.inc()


def on_connect(client, _userdata, _flags, result_code):
    """The callback for when the client receives a CONNACK response from the server."""
    print(f"Connected to MQTT broker with result code: {result_code}")
    client.subscribe("home/onair")


def on_message(_client, _userdata, msg):
    """The callback for when a PUBLISH message is received from the server."""
    print(msg.topic + " " + str(msg.payload))
    new_state = msg.payload.decode().upper()
    if new_state in State.__members__:
        set_state(State[new_state])
    else:
        print(f"Unknown state requested: {new_state}")


# Initialize the GPIO
GPIO.setmode(GPIO.BCM)
init_gpio(PIN)

# Register MQTT callbacks and connect to the MQTT broker
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(MQTT_BROKER, 1883, 60)
mqtt_client.loop_forever()
