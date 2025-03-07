import sys
import unittest
from dvhcalculator import DvhCurve, DicomDatabase, dvh_extractor
import pydicom
import json
import os
from dicompylercore import dicomparser, dvhcalc
import logging

logger = logging.getLogger('dvhcalculator-test')

logging.basicConfig(
    format = '%(asctime)s %(module)s %(levelname)s: %(message)s',
    level = logging.DEBUG,
    stream = sys.stdout)

class TestDvhCalculator(unittest.TestCase):
    def test_dvh_calculator(self):

        dcmHeader = pydicom.dcmread('tests/resources/dicom/RP.PYTIM05_PS2.dcm')

        dicomDb = DicomDatabase()
        dicomDb.parseFolder('tests/resources/dicom')

        folderPath = "tests/resources/dvh_json"
        if not os.path.exists(folderPath):
            os.mkdir(folderPath)

        dvh_extractor.batchProcessPlans(dicomDb, folderPath)

        with open('tests/resources/dvh_json/1.2.246.352.71.5.2088656855.377051.20110920152006.json', 'r') as f:
            dvhJson = json.load(f)

        structures = dvhJson['structures_dvh']
        dvhCurves = list()

        for structure in structures:
            dvhCurves.append(DvhCurve(structure))

        for dvhCurve in dvhCurves:
            logger.info('Dmin  = ' + str(dvhCurve.min))
            logger.info('Dmean = ' + str(dvhCurve.mean))
            logger.info('Dmax  = ' + str(dvhCurve.max))
            logger.info("volume= " + str(dvhCurve.volume))
            logger.info("color = " + str(dvhCurve.color))
            logger.info("plannedDose = " + str(dvhCurve.plannedDose))
            logger.info('D2%   = ' + str(dvhCurve.dValueRelative(2)))
            logger.info('V20Gy = ' + str(dvhCurve.vValue(20)))

        tags = dcmHeader.keys()
        # for tag in tags:
            # logger.info("%s - %s" % (tag,pydicom.datadict.keyword_for_tag(tag)))

        dcmHeader[0x300c,0x60][0]

        dcmHeader = pydicom.dcmread("tests/resources/dicom/RD.PYTIM05_.dcm")

        tags = dcmHeader.keys()
        # for tag in tags:
            # logger.info("%s - %s" % (tag,pydicom.datadict.keyword_for_tag(tag)))

        dcmHeader[0x300c,0x2][0]

        dcmHeader = pydicom.dcmread('tests/resources/dicom/RS.PYTIM05_.dcm')
        dcmHeader[0x3006,0x10][0][0x20,0x52].value

        dcmHeader

        dicomDb = DicomDatabase()
        dicomDb.parseFolder('tests/resources/dicom')

        for ptid in dicomDb.getPatientIds():
            patient = dicomDb.getPatient(ptid)
            planUid = list(patient.getRTPlans())[0]
            
            rtplan = patient.getRTPlan(planUid)
            logger.debug(rtplan.plannedDose)
            rtstruct = patient.getStructForPlan(rtplan)
            rtdose = patient.getDoseForPlan(rtplan)
            logger.debug(patient)

        # i.e. Get a dict of structure information
        dp_rtstruct = dicomparser.DicomParser(rtstruct.getFileLocation())
        structures = dp_rtstruct.GetStructures()

        structureId = None

        for i in structures:
            structure = structures[i]
            if not structure["empty"]:
                structureId = structure["id"]
                
                # now calculate DVH
                calcdvh = dvhcalc.get_dvh(rtstruct.getFileLocation(), rtdose.getFileLocation(), structureId)
                logger.debug(calcdvh.bincenters)

if __name__ == '__main__':
    unittest.main()