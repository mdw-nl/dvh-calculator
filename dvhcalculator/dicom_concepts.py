import os
import pydicom
import logging

logger = logging.getLogger(__name__)

class DicomDatabase:
    def __init__(self):
        self.patient = dict()
    
    def parseFolder(self, folderPath):
        for root, subdirs, files in os.walk(folderPath):
            for filename in files:
                file_path = os.path.join(root, filename)
                if(file_path.endswith(".dcm")):
                    dcmHeader = pydicom.dcmread(file_path)
                    patientId = dcmHeader[0x10,0x20].value
                    patient = self.getOrCreatePatient(patientId)
                    patient.addFile(file_path, dcmHeader)

    def getOrCreatePatient(self, patientId):
        if not (patientId in self.patient):
            self.patient[patientId] = Patient()
        return self.patient[patientId]
    
    def countPatients(self):
        return len(self.patient)
    
    def getPatient(self, patientId):
        return self.patient[patientId]
    
    def getPatientIds(self):
        return self.patient.keys()
    
    def doesPatientExist(self, patientId):
        # return self.patient.has_key(patientId)
        return patientId in self.patient

class Patient:
    def __init__(self):
        self.ct = dict()
        self.rtstruct = dict()
        self.rtplan = dict()
        self.rtdose = dict()
        
        self.id = None
        self.name = None
        self.headerExtracted = False
        
    def setPatientInfo(self, dcmHeader):
        self.id = dcmHeader[0x10,0x20].value
        self.name = dcmHeader[0x10,0x10].value
        self.headerExtracted = True

    def addFile(self, filePath, dcmHeader):
        # set dicom header data if not done yet
        if not self.headerExtracted:
            self.setPatientInfo(dcmHeader)
        
        # read additional header data for current file at hand
        modality = dcmHeader[0x8,0x60].value
        sopInstanceUid = dcmHeader[0x8,0x18].value
        seriesInstanceUid = dcmHeader[0x20,0xe].value
        
        # decide modality and add the file accordingly
        if(modality == "CT"):
            if not (seriesInstanceUid in self.ct):
                self.ct[seriesInstanceUid] = CT()
            myCT = self.ct[seriesInstanceUid]
            myCT.addCtSlice(filePath, dcmHeader)
        if(modality == "RTSTRUCT"):
            struct = RTStruct(filePath, dcmHeader)
            self.rtstruct[sopInstanceUid] = struct
        if(modality == "RTPLAN"):
            plan = RTPlan(filePath, dcmHeader)
            self.rtplan[sopInstanceUid] = plan
        if(modality == "RTDOSE"):
            dose = RTDose(filePath, dcmHeader)
            self.rtdose[sopInstanceUid] = dose    
    def getId(self):
        return self.id
    def getName(self):
        return self.name
    def countCTScans(self):
        return len(self.ct)
    def countRTStructs(self):
        return len(self.rtstruct)
    
    def getCTScan(self, seriesInstanceUid):
        if seriesInstanceUid is not None:
            if self.doesCTExist(seriesInstanceUid):
                return self.ct[seriesInstanceUid]
        return None
    def getRTStruct(self, sopInstanceUid):
        return self.rtstruct[sopInstanceUid]
    def getRTPlan(self, sopInstanceUid):
        return self.rtplan[sopInstanceUid]
    def getRTDose(self, sopInstanceUid):
        return self.rtdose[sopInstanceUid]
    
    def getCTScans(self):
        return self.ct.keys()
    def getRTStructs(self):
        return self.rtstruct.keys()
    def getRTPlans(self):
        return self.rtplan.keys()
    
    def doesCTExist(self, seriesInstanceUid):
        return seriesInstanceUid in self.ct
    def doesRTStructExist(self, sopInstanceUid):
        return sopInstanceUid in self.rtstruct
    
    def getCTForRTStruct(self, rtStruct):
        # get CT UID from RTStruct object
        if rtStruct.getReferencedCTUID() in self.ct:
            return self.getCTScan(rtStruct.getReferencedCTUID())
        else:
            # Alternative mode, do linking based on frameOfReference
            frameOfRef = rtStruct.getReferencedFrameOfReferenceCT()
            if frameOfRef is not None:
                # This means we have to loop over all CT scans, and search for the matching FrameOfRef
                for myCt in self.ct.values():
                    if myCt.getFrameOfReference()==frameOfRef:
                        return myCt
                return None
    def getStructForPlan(self, rtPlan):
        if rtPlan.getReferencedStructUid() in self.rtstruct:
            return self.rtstruct[rtPlan.getReferencedStructUid()]
        else:
            return None
    def getDoseForPlan(self, rtPlan):
        for myDose in self.rtdose.values():
            logger.debug(myDose)
            if myDose.getReferencedPlanUid() == rtPlan.getUid():
                logger.debug(myDose.getReferencedPlanUid())
                dose = pydicom.dcmread(myDose.getFileLocation())
                logger.debug(dose.get(['3004', '000a']).value)
                if dose.get(['3004', '000a']).value == "PLAN":
                    return myDose
        return None

    def __str__(self):
        return "Patient: " + self.id + " - CT: " + str(self.countCTScans()) + " - RTStruct: " + str(self.countRTStructs()) + " - RTPlan: " + str(self.rtplan) + " - RTDose: " + str(self.rtdose)

class CT:
    def __init__(self):
        self.filePath = list()
        self.frameOfRef = None
        self.headerExtracted = False
    def setCtInfo(self, dcmHeader):
        self.frameOfRef = dcmHeader[0x20,0x52].value
        self.headerExtracted = True
    def addCtSlice(self, filePath, dcmHeader):
        if not self.headerExtracted:
            self.setCtInfo(dcmHeader)
        self.filePath.append(filePath)
    def getSlices(self):
        return self.filePath
    def getSliceCount(self):
        return len(self.filePath)
    def getFrameOfReference(self):
        return self.frameOfRef

class RTStruct:
    def __init__(self, filePath, dcmHeader):
        self.filePath = filePath
        
        self.referencedFrameOfReference = None
        self.referencedCtUid = None
        
        self.readHeader(dcmHeader)
        
    def readHeader(self, dcmHeader):
        # get Referenced Frame of Reference
        if len(list(dcmHeader[0x3006,0x10])) > 0:
            self.referencedFrameOfReference = dcmHeader[0x3006,0x10][0][0x20,0x52].value
        
        # get referenced CT UID
        if len(list(dcmHeader[0x3006,0x10])) > 0:
            refFrameOfRef = (dcmHeader[0x3006,0x10])[0]
            if len(list(refFrameOfRef[0x3006, 0x0012])) > 0:
                rtRefStudy = (refFrameOfRef[0x3006, 0x0012])[0]
                if len(list(rtRefStudy[0x3006,0x14])) > 0:
                    rtRefSerie = (rtRefStudy[0x3006,0x14])[0]
                    self.referencedCtUid = rtRefSerie[0x20,0xe].value
    
    def getReferencedFrameOfReferenceCT(self):
        return self.referencedFrameOfReference
    def getReferencedCTUID(self):
        return self.referencedCtUid
    def getFileLocation(self):
        return self.filePath
    
class RTPlan:
    def __init__(self, filePath, dicomHeader):
        self.filePath = filePath
        
        self.label = None
        self.name = None
        self.referencedStructUid = None
        self.uid = None
        self.plannedDose = None
        
        self.readHeader(dicomHeader)
    
    def readHeader(self, dcmHeader):
        self.label = dcmHeader[0x300A,0x2].value
        if ([0x300A, 0x3] in dcmHeader
                and len(list(dcmHeader[0x300A, 0x3])) > 0):
            self.name = dcmHeader[0x300A,0x3].value
        self.uid = dcmHeader[0x8,0x18].value
    
        # get referenced struct UID
        if len(list(dcmHeader[0x300c,0x60])) > 0:
            refStruct = dcmHeader[0x300c,0x60][0]
            self.referencedStructUid = refStruct[0x8,0x1155].value
        
        # get planned dose value
        if ([0x300a, 0x10] in dcmHeader
                and len(list(dcmHeader[0x300a, 0x10])) > 0):
            doseSeq = dcmHeader[0x300a,0x10][0]
            self.plannedDose = doseSeq[0x300a,0x26].value

    def getReferencedStructUid(self):
        return self.referencedStructUid
    def getLabel(self):
        return self.label
    def getName(self):
        return self.name
    def getUid(self):
        return self.uid
    def getFileLocation(self):
        return self.filePath
    def __str__(self):
        return "RTPlan: " + self.filePath + " - " + self.label + " - " + self.name + " - " + self.referencedStructUid + " - " + self.uid + " - " + self.plannedDose

class RTDose:
    def __init__(self, filePath, dicomHeader):
        self.filePath = filePath
        
        self.type = None
        self.units = None
        self.referencedPlanUid = None
        
        self.readHeader(dicomHeader)
    
    def readHeader(self, dcmHeader):
        self.units = dcmHeader[0x3004,0x2].value
        self.type = dcmHeader[0x3004,0x4].value
    
        # get referenced struct UID
        if len(list(dcmHeader[0x300C,0x2])) > 0:
            refStruct = dcmHeader[0x300C,0x2][0]
            self.referencedPlanUid = refStruct[0x8,0x1155].value
            
    def getReferencedPlanUid(self):
        return self.referencedPlanUid
    def getType(self):
        return self.type
    def getUnits(self):
        return self.units
    def getFileLocation(self):
        return self.filePath
    def __str__(self):
        return "RTDose: " + self.filePath + " - " + self.type + " - " + self.units + " - " + self.referencedPlanUid