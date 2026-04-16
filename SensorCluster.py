from Sensor import *
from NoiseSource import *
from random import uniform as randfloat
from scipy.optimize import minimize

SOUND_SPEED = 340

class SensorCluster:
    """
    Кластер датчиков. 
    Отвечает за агрегацию данных со всех датчиков и расчёты.
    """

    sensors: list[Sensor]  # Массив датчиков
    inaccuracy: float # Разброс случайной погрешности времени прихода на датчики
    randomization: bool  # При True применяется случайное число, при False максимально возможное
    events: dict  # Сработавшие датчики и время

    def __init__(self, sensors: list[Sensor] = []):
        self.sensors = sensors
        self.inaccuracy = 0.002
        self.randomization = True
        self.events = {}

    def get(self, id: int) -> Sensor:
        """
        Доступ к датчику по id.
        """

        return next(filter(lambda sensor: sensor.id == id, self.sensors))
    
    def delay(self, id1: int, id2: int) -> float:
        """
        Задержка прихода между двумя датчиками.
        """

        return self.events[id1] - self.events[id2]
    
    def phi(self, noise_coordinates: list[float]) -> float:
        """
        Функционал для минимизации.
        """

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
        """
        Локализация источника через минимизацию функционала.
        """

        result = minimize(
            fun = self.phi,
            x0 = [0, 0],
            method='Nelder-Mead',
            tol=1e-10
        )

        return result.x

    def record(self, source: NoiseSource) -> None:
        """
        Записать источник звука (ИЗ) на кластер.
        """

        for sensor in self.sensors:
            # Дистанция от датчика до ИЗ
            distance = np.sqrt((sensor.coordinates[0] - source.coordinates[0])**2 + (sensor.coordinates[1] - source.coordinates[1])**2)
            # Расчётное время прихода
            ideal_arrival = distance / SOUND_SPEED

            # Погрешность прихода
            if self.randomization:
                arrival_inaccuracy = randfloat(-self.inaccuracy*ideal_arrival, +self.inaccuracy*ideal_arrival)
            else:
                arrival_inaccuracy = +self.inaccuracy*ideal_arrival

            # Время прихода с учётом погрешности
            arrival = ideal_arrival + arrival_inaccuracy

            # Генерация импульса Берлаге
            berlage = BerlageImpulse()
            berlage.build(0, 7, 350)

            # Передать импульс на сенсор и задать время прихода
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

            # Если обнаружено событие, записать и отправить
            if response["event"]: 
                it["event_marks"].append(sensor.id)
                if sensor.id not in self.events:
                    self.events[sensor.id] = sensor.t


        # Если все датчики сработали, рассчитать и отправить координаты ИЗ
        if len(self.events) == len(self.sensors):
            coords = self.localize_source()
            it["location"].append(coords[0])
            it["location"].append(coords[1])
            self.events = {}
            print(coords)
        
        return it