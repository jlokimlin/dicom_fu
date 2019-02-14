#!/usr/bin/env python3
import pandas as pd
import pydicom
import numpy as np
import os
import logging

from pandas import DataFrame
from pydicom import FileDataset
import argparse
import tqdm

MR_STORAGE_SOP = '1.2.840.10008.5.1.4.1.1.4'
CT_STORAGE_SOP = '1.2.840.10008.5.1.4.1.1.2'
MR_TAGS_OF_INTEREST = {
    'SeriesInstanceUID': str,
    'StudyInstanceUID': str,
    'PatientName': str,
    'PatientID': str,
    'Modality': str,
    'PatientSex': str,
    'SliceThickness': float,
    'PixelSpacing': lambda x: np.array(x).astype(np.float32),
    'Rows': int,
    'Columns': int,
    'Manufacturer': str,
    'InstitutionName': str,
    'StudyDescription': str,
    'SeriesDescription': str,
    'MagneticFieldStrength': float,
    'EchoTime': float,
    'InversionTime': float,
    'ImagedNucleus': str,
    'ImagingFrequency': float,
    'NumberOfAverages': int,
    'SpacingBetweenSlices': float,
    'EchoTrainLength': int,
    'AccessionNumber': str,
    'ImageType': str,
    'PercentSampling': float,
    'PercentPhaseFieldOfView': float,
    'PixelBandwidth': float,
    'ContrastBolusAgent': str,
    'ReconstructionDiameter': float
}
CT_TAGS_OF_INTEREST = {
    'SeriesInstanceUID': str,
    'StudyInstanceUID': str,
    'PatientName': str,
    'PatientID': str,
    'Modality': str,
    'PatientSex': str,
    'SliceThickness': float,
    'PixelSpacing': lambda x: np.array(x).astype(np.float32),
    'ConvolutionKernel': str,
    'Rows': int,
    'Columns': int,
    'Manufacturer': str,
    'InstitutionName': str,
    'StudyDescription': str,
    'SeriesDescription': str,
    'KVP': float,
    'Exposure': int,
    'AccessionNumber': str,
    'ImageType': str
}

logger = logging.getLogger('explorer')


def get_mr_info(folder):
    dicom_files = [f for f in os.listdir(folder)]
    found_mr = False
    for f in dicom_files:
        try:
            im: FileDataset = pydicom.dcmread(os.path.join(folder, f))
        except pydicom.errors.InvalidDicomError:
            continue
        if im.SOPClassUID.startswith(MR_STORAGE_SOP):
            found_mr = True
            break
    if not found_mr:
        return None
    try:
        modality = im.Modality
        if "MR" not in modality.upper():
            logger.warning(
                "Header mismatch: modality information {} in header"
                " does not match storage class MR in file {}".format(
                    modality, os.path.join(
                        folder, f)))
    except KeyError:
        logger.warning(
            'No modality information found in MR image file: {}'.format(
                os.path.join(
                    folder, f)))

    info = {}
    for key in MR_TAGS_OF_INTEREST.keys():
        if key in im:
            try:
                info[key] = MR_TAGS_OF_INTEREST[key](
                    im.data_element(key).value)
            except ValueError:
                info[key] = np.nan
        else:
            info[key] = np.nan

    info['Location on disk'] = folder
    return info


def get_ct_info(folder):
    dicom_files = [f for f in os.listdir(folder)]
    found_ct = False
    for f in dicom_files:
        try:
            im: FileDataset = pydicom.dcmread(os.path.join(folder, f))
        except pydicom.errors.InvalidDicomError:
            continue
        if im.SOPClassUID.startswith(CT_STORAGE_SOP):
            found_ct = True
            break
    if not found_ct:
        return None
    try:
        modality = im.Modality
        if "CT" not in modality.upper():
            logger.warning(
                "Header mismatch: modality information {} in header"
                " does not match storage class CT in file {}".format(
                    modality, os.path.join(
                        folder, f)))
    except KeyError:
        logger.warning(
            'No modality information found in CT image file: {}'.format(
                os.path.join(
                    folder, f)))

    info = {}
    for key in CT_TAGS_OF_INTEREST.keys():
        if key in im:
            try:
                info[key] = CT_TAGS_OF_INTEREST[key](
                    im.data_element(key).value)
            except ValueError:
                info[key] = np.nan
        else:
            info[key] = np.nan

    info['Location on disk'] = folder
    return info


def summarize(folder, save_output=None):
    info_df: DataFrame = pd.DataFrame()
    for r, c, f in os.walk(folder):
        if len(c) == 0:
            info_df = info_df.append(get_mr_info(r), ignore_index=True)
            info_df = info_df.append(get_ct_info(r), ignore_index=True)
    if save_output is not None:
        info_df.to_csv(save_output)
    return info_df


def find_leaves(folder):
    lst = []
    for r, c, f in os.walk(folder):
        if len(c) != 0 and len(f) != 0:
            logger.warning(
                'Directory structure may not be standard! Found files in a non-leaf directory {}'.format(r))
        if len(c) == 0:
            lst.append(r)
    return lst


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "root", help="the root directory containing dicom files")
    parser.add_argument(
        "--output_file",
        "-o",
        help="name of the output file",
        default='summary.csv')
    args = parser.parse_args()
    root = args.root
    output_file = args.output_file
    print('Analyzing file structure')
    leaves = find_leaves(root)
    df = pd.DataFrame()
    print('Analyzing volumes')
    for l in tqdm.tqdm(leaves, ascii=True):
        ct_info = get_ct_info(l)
        df = df.append(ct_info, ignore_index=True)
        if ct_info is None:
            mr_info = get_mr_info(l)
            df = df.append(mr_info, ignore_index=True)
    df.to_csv(output_file)
