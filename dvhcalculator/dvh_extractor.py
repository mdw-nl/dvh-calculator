import json
import logging
import os.path

from dicompylercore import dicomparser, dvhcalc

from .check_jsonable import log_unjsonable

def batchProcessPlans(dicomDb, folderPath):
    for ptid in dicomDb.getPatientIds():
        patient = dicomDb.getPatient(ptid)
        for planUid in patient.getRTPlans():
            rtplan = patient.getRTPlan(planUid)
            rtstruct = patient.getStructForPlan(rtplan)
            rtdose = patient.getDoseForPlan(rtplan)
            try:
                print('processing %s' % planUid)
                process_and_save_dvh(folderPath, planUid, rtplan, rtdose,
                                     rtstruct, patient)
            except Exception as e:
                logging.error(
                    'something occurred processing plan %s' % planUid)
                logging.error(e)
                return planUid, False
            return planUid, True


def process_and_save_dvh(folderPath, planUid, rtplan, rtdose, rtstruct,
                         patient):
    planOut = get_dvh_dict(planUid, rtplan, rtdose, rtstruct)
    fileName = os.path.join(folderPath + ('/%s/' % patient.getId()),
                            '%s.json' %
                            planUid)
    with open(fileName, 'w') as outfile:
        try:
            json.dump(planOut, outfile)
        except TypeError as e:
            log_unjsonable(planOut)
            raise e


def get_dvh_dict(planUid, rtplan, rtdose, rtstruct):
    structureListOut = processDvhForSet(rtstruct, rtdose, rtplan)
    planOut = {
        "planInstanceUid": planUid,
        "structures_dvh": structureListOut
    }
    return planOut


def processDvhForSet(rtStruct, rtDose, rtPlan):
    structures = dicomparser.DicomParser(rtStruct.getFileLocation()).GetStructures()
    
    output = list()

    for i in structures:
        structure = structures[i]
        if not structure["empty"]:
            try:
                print('doing struct {} of {}...'.format(i, len(structures)))
                calcdvh = dvhcalc.get_dvh(rtStruct.getFileLocation(),
                                          rtDose.getFileLocation(),
                                          structure["id"])
                print('succes')
                structOut = {
                    "structureName": structure["name"],
                    "min": calcdvh.min,
                    "mean": calcdvh.mean,
                    "max": calcdvh.max,
                    "volume": int(calcdvh.volume),
                    "color": structure["color"].tolist(),
                    "plannedDose": rtPlan.plannedDose,
                    "dvh_d": calcdvh.bincenters.tolist(),
                    "dvh_v": calcdvh.counts.tolist()
                }
                output.append(structOut)
            except Exception as e:
                print('failed for struct %s' % structure)
                logging.exception(e)
    return output