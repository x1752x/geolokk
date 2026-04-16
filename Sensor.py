from GaussianNoiseGenerator import *
from BerlageImpulse import *
from Detector import *

class Sensor:
    id: int
    coordinates: list[float]

    next_event: int = -1
    generator: GaussianNoiseGenerator

    impulse: BerlageImpulse
    impulse_n: int = 0

    detector: Detector

    t: int = -1

    def __init__(self, coordinates: list[float], id: int):
        self.id = id
        self.coordinates = coordinates
        self.generator = GaussianNoiseGenerator(0, 0.0005)
        self.detector = Detector(30, 300, 2)
        self.n = 0

    def generate_once(self):
        it = {}

        self.t += 10
        if self.next_event != -1 and self.t >= self.next_event:
            it["response"] = self.impulse.w[self.impulse_n] + self.generator.generate_once()
            self.impulse_n += 1
            if self.impulse_n >= len(self.impulse.w):
                self.impulse_n = 0
                self.next_event = -1
        else:
            it["response"] = self.generator.generate_once()

        it["event"] = self.detector.detect(it["response"])

        self.n += 10

        return it