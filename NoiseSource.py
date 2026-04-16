class NoiseSource:
    id: int
    coordinates: list[float]

    def __init__(self, coordinates: list[float], id: int):
        self.id = id
        self.coordinates = coordinates