try:
    import RPi.GPIO as GPIO
except:
    import FakeRPi.GPIO as GPIO
import uuid


class Raspi(object):

    def __init__(self, outPin, name):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(outPin, GPIO.OUT)
        self.outPin = outPin
        self.uuid = uuid.uuid4()
        self.name = name
        #GPIO.setup(SENSOR_PIN, GPIO.IN)

    def changeOutPin(self, value):
        GPIO.output(self.outPin, value)
