import unittest
from dvhcalculator import DvhCurve, DicomDatabase, dvh_extractor
import pydicom
import json
import os
from dicompylercore import dicomparser, dvhcalc
import matplotlib.pyplot as plt

class TestDvhCalculator(unittest.TestCase):
    def test_dvh_calculator(self):
        print(os.getcwd())

        dcmHeader = pydicom.dcmread('tests/resources/dicom/RP.1.2.246.352.71.5.2088656855.377051.20110920152006.dcm')

        dicomDb = DicomDatabase()
        dicomDb.parseFolder('./resources/dicom')

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
            dvhCurve.plot()
            print('Dmin  = ' + str(dvhCurve.min))
            print('Dmean = ' + str(dvhCurve.mean))
            print('Dmax  = ' + str(dvhCurve.max))
            print("volume= " + str(dvhCurve.volume))
            print("color = " + str(dvhCurve.color))
            print("plannedDose = " + str(dvhCurve.plannedDose))
            print('D2%   = ' + str(dvhCurve.dValueRelative(2)))
            print('V20Gy = ' + str(dvhCurve.vValue(20)))

        tags = dcmHeader.keys()
        for tag in tags:
            print("%s - %s" % (tag,pydicom.datadict.keyword_for_tag(tag)))

        dcmHeader[0x300c,0x60][0]

        dcmHeader = pydicom.dcmread("tests/resources/dicom/RD.1.2.246.352.71.7.2088656855.452097.20110920152341.dcm")

        tags = dcmHeader.keys()
        for tag in tags:
            print("%s - %s" % (tag,pydicom.datadict.keyword_for_tag(tag)))

        dcmHeader[0x300c,0x2][0]

        dcmHeader = pydicom.dcmread('tests/resources/dicom/RS.1.2.246.352.71.4.2088656855.2402030.20110920095607.dcm')
        dcmHeader[0x3006,0x10][0][0x20,0x52].value

        dcmHeader

        dicomDb = DicomDatabase()
        dicomDb.parseFolder('tests/resources/dicom')

        for ptid in dicomDb.getPatientIds():
            patient = dicomDb.getPatient(ptid)
            planUid = list(patient.getRTPlans())[0]
            
            rtplan = patient.getRTPlan(planUid)
            print(rtplan.plannedDose)
            rtstruct = patient.getStructForPlan(rtplan)
            rtdose = patient.getDoseForPlan(rtplan)

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
                
                plt.plot(calcdvh.bincenters, calcdvh.counts, color=(structure['color']/255), label=structure['name'])
                plt.title("Dose-volume histogram")
                plt.xlabel("Dose (Gray)")
                plt.ylabel("Volume (cc)")
                plt.legend()
                plt.show()

if __name__ == '__main__':
    unittest.main()