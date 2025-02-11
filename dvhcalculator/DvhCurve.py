import matplotlib.pyplot as plt
import numpy as np

class DvhCurve():

    def __init__(self, varIn = None):
        if varIn == None:
            return
        self._name = varIn["structureName"]
        self._min = varIn["min"]
        self._mean = varIn["mean"]
        self._max = varIn["max"]
        self._color = np.asarray(varIn["color"])
        self._plannedDose = varIn["plannedDose"]
        self._doseVector = np.asarray(varIn["dvh_d"])
        self._volumeVector = np.asarray(varIn["dvh_v"])

    @property
    def doseVector(self):
        return self._doseVector

    @property
    def volumeVector(self):
        return self._volumeVector

    @property
    def min(self):
        return self._min
    
    @property
    def mean(self):
        return self._mean
    
    @property
    def max(self):
        return self._max

    @property
    def volume(self):
        return self.volumeVector[0]

    @property
    def color(self):
        return self._color

    @property
    def name(self):
        return self._name

    @property
    def plannedDose(self):
        return self._plannedDose

    def plot(self):
        plt.plot(self.doseVector, self.volumeVector, label=(self.name), color = self.color/255)  # TODO implement color
        plt.title("Dose-volume histogram")
        plt.xlabel("Dose (Gray)")
        plt.ylabel("Volume (cc)")
        plt.legend()
        plt.show()

    def dValue(self, limit):
        idx = (np.abs(self.volumeVector-limit)).argmin()
        return self.doseVector[idx]
    
    def dValueRelative(self, limit):
        absLimit = (limit / 100) * self.volumeVector[0]
        return self.dValue(absLimit)
        
    def vValue(self, limit):
        idx = (np.abs(self.doseVector-limit)).argmin()
        return self.volumeVector[idx]

    def vValueRelative(self, limit):
        absLimit = (limit/100) * self.plannedDose
        return self.vValue(absLimit)

    def getAttributes(self):
        attributes = [attr for attr in dir(self)
            if not attr.startswith("__")]
        return attributes