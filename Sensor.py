from GaussianNoiseGenerator import *
from BerlageImpulse import *
from Detector import *

class Sensor:
    id: int
    coordinates: list[float]

    next_event: int  # Время прихода следующего события
    generator: GaussianNoiseGenerator  # Генератор шума

    impulse: np.ndarray  # Импульс для записи
    impulse_n: int  # Счётчик отсчётов импульса

    detector: Detector  # Детектор STA/LTA

    t: int  # Внутреннее время (мс)

    def __init__(self, coordinates: list[float], id: int):
        self.id = id
        self.coordinates = coordinates
        self.next_event = -1
        self.generator = GaussianNoiseGenerator(0, 10)
        self.impulse_n = 0
        self.detector = Detector(100, 2000, 2)
        self.t = 0

    def generate_once(self):
        it = {}
        
        self.t += 10

        if self.next_event != -1 and self.t >= self.next_event:
            it["response"] = self.impulse[self.impulse_n] + self.generator.generate_once()
            self.impulse_n += 1
            if self.impulse_n >= len(self.impulse):
                self.impulse_n = 0
                self.next_event = -1
        else:
            it["response"] = self.generator.generate_once()

        it["event"] = self.detector.detect(it["response"])

        return it