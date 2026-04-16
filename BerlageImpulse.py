import numpy as np

class BerlageImpulse:
    def __init__(self, b = 5, n = 6, omega = 2 * 3.14 * 5):
        self.b = b
        self.n = n
        self.omega = omega
        self.x0 = 0

    def berlage(self, t, b, n, omega):
        ts = t - self.x0
        return np.where(t < self.x0, 0, ts**n * np.exp(-b*ts) * np.sin(omega*ts))

    def build(self, start, end, n):
        self.t = np.linspace(start, end, n)
        self.w = self.berlage(self.t, self.b, self.n, self.omega)