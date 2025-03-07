import sys
from .dicom_concepts import DicomDatabase, Patient, RTStruct, RTPlan, RTDose, CT
from .DvhCurve import DvhCurve
import logging

logFormatter = logging.Formatter(fmt="%(asctime)s,%(msecs)03d %(name)s %(lineno)d %(levelname)s %(message)s", datefmt='%Y-%m-%d %H:%M:%S')
rootLogger = logging.getLogger()

fileHandler = logging.FileHandler(filename='dvhcalculator.log', mode='a')
fileHandler.setFormatter(logFormatter)
rootLogger.addHandler(fileHandler)

consoleHandler = logging.StreamHandler(sys.stdout)
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)
rootLogger.setLevel(logging.DEBUG)
