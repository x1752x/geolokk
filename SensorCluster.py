from Sensor import *
from NoiseSource import *
from random import uniform as randfloat
from scipy.optimize import minimize

SOUND_SPEED = 340

class SensorCluster:
    sensors: list[Sensor]
    inaccuracy: float = 0.002
    randomization: bool = True
    events: dict

    def __init__(self, sensors: list[Sensor] = []):
        self.sensors = sensors
        self.events = {}

    def get(self, id: int) -> Sensor:
        return next(filter(lambda sensor: sensor.id == id, self.sensors))
    
    def delay(self, id1: int, id2: int) -> float:
        return self.events[id1] - self.events[id2]
    
    def phi(self, noise_coordinates: list[float]) -> float:
        it = 0
        n = len(self.sensors)
        for i in range(n-1):
            for j in range(i+1, n):
                distance_i = np.sqrt((self.get(i).coordinates[0] - noise_coordinates[0])**2 + 
                               (self.get(i).coordinates[1] - noise_coordinates[1])**2)
                
                distance_j = np.sqrt((self.get(j).coordinates[0] - noise_coordinates[0])**2 + 
                               (self.get(j).coordinates[1] - noise_coordinates[1])**2)
                
                diff = distance_i - distance_j - SOUND_SPEED * (self.delay(i, j) / 1000)
                it += diff**2
        return it
    
    def localize_source(self):
        result = minimize(
            fun = self.phi,
            x0 = [0, 0],
            method='Nelder-Mead',
            tol=1e-10
        )

        return result.x

    def record(self, source: NoiseSource) -> None:
        for sensor in self.sensors:
            distance = np.sqrt((sensor.coordinates[0] - source.coordinates[0])**2 + (sensor.coordinates[1] - source.coordinates[1])**2)
            ideal_arrival = distance / SOUND_SPEED
            if self.randomization:
                arrival_inaccuracy = randfloat(-self.inaccuracy*ideal_arrival, +self.inaccuracy*ideal_arrival)
            else:
                arrival_inaccuracy = +self.inaccuracy*ideal_arrival
            arrival = ideal_arrival + arrival_inaccuracy

            """
            N = L / T
            L = N * T
            T = L / N
            """
            berlage = BerlageImpulse()
            berlage.build(0, 7, 350)

            sensor.impulse = berlage
            sensor.next_event = sensor.t + arrival*1000

    def generate_once(self):
        it = {
            "sensor_responses": {},
            "event_marks": [],
            "location": []
        }

        for sensor in self.sensors:
            response = sensor.generate_once()
            it["sensor_responses"][sensor.id] = response["response"]
            if response["event"]: 
                it["event_marks"].append(sensor.id)
                if sensor.id not in self.events:
                    self.events[sensor.id] = sensor.n
        
        if len(self.events) == len(self.sensors):
            coords = self.localize_source()
            it["location"].append(coords[0])
            it["location"].append(coords[1])
            self.events = {}
            print(coords)
        
        return it