import numpy as np

from numpy.typing import DTypeLike
from typing import Any

import struct

class Trace:
    header: dict[str, Any] = {}
    timeline: np.ndarray
    values: np.ndarray

    def _sample_type(self, x: int) -> DTypeLike | None:
        match x:
            case 2:
                return np.short
            case 4:
                return np.int32
            case 4100:
                return np.float32
            case 4101:
                return np.double
    
    def __init__(self, filename: str):
        with open(filename, 'rb') as file:
            header = file.read(42)
            values = struct.unpack("<h4sffdbbbbbbihihbb", header)
            keys = ("ID", "Reserv", "Lat", "Lon", "Scale", "Year", "Month", 
                    "Day", "Hour", "Minute", "Second", "MicroSec", "SamplRate", 
                    "SamplNum", "SamplType", "TrNum", "Reserved")
            self.header = dict(zip(keys, values))
            self.header["SamplType"] = self._sample_type(self.header["SamplType"])

            self.timeline = np.linspace(0, self.header['SamplNum'] / self.header['SamplRate'] * 1000, self.header['SamplNum'])

            sample_size = np.dtype(self.header["SamplType"]).itemsize
            total_size = self.header["SamplNum"] * sample_size

            data = file.read(total_size)

            self.values = np.frombuffer(data, dtype = self.header["SamplType"])