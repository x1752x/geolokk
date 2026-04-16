import numpy as np

class GaussianNoiseGenerator:
    mean: float
    std: float

    def __init__(self, mean: float, std: float):
        self.mean = mean
        self.std = std

    def generate_once(self) -> float:
        return np.random.normal(loc = self.mean, scale = self.std)