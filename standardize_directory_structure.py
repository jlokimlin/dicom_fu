#!/usr/bin/env python3
import os
import pydicom
import logging
import shutil
import argparse
import sys
import errno


class FileCounter:

    def __init__(self, printing_interval=100):
        self.counter = 0
        self.printing_interval = printing_interval

    def update(self, value=1):
        self.counter += value
        if self.counter % self.printing_interval == 0:
            sys.stdout.write(
                '\r Number of files moved: {}'.format(
                    self.counter))
            sys.stdout.flush()


def remove_empty_subdirs(root):
    """
    removes empty subdirectories recursively under root. Does not remove root if it is empty
    :param root: path to the root directory
    """
    for s in os.scandir(root):
        if s.is_dir():
            remove_empty_subdirs(os.path.join(root, s))
            try:
                os.rmdir(os.path.join(root, s))
            except OSError as e:
                if e.errno == errno.ENOTEMPTY:
                    logger.debug(
                        'path {} is not empty'.format(
                            os.path.join(
                                root, s)))
                else:
                    logger.error(e)


def standardize_structure_in_place(source):
    """
    Moves dicom files around in the source directory to conform to the structure patientid/studyid/seriesid/dicom.dcm.
    This is done in-place.
    :param source: root directory containing the dicom files
    """
    counter = FileCounter()
    filestruct = {'other': [], 'dicoms': {'UNCATEGORIZED': []}}
    # Record the current directory structure
    logger.info('Analyzing file structure')
    for r, c, f in os.walk(source):
        for filename in f:
            try:
                im = pydicom.dcmread(os.path.join(r, filename))
            except pydicom.errors.InvalidDicomError:
                filestruct['other'] += [os.path.join(r, filename)]
                continue
            try:
                pid = im.PatientID
                study = im.StudyInstanceUID
                series = im.SeriesInstanceUID
                key = tuple([pid, study, series])
                if key in filestruct['dicoms']:
                    filestruct['dicoms'][key] += [os.path.join(r, filename)]
                else:
                    filestruct['dicoms'][key] = [os.path.join(r, filename)]
            except KeyError:
                filestruct['dicoms']['UNCATEGORIZED'] += [
                    os.path.join(r, filename)]
    logger.info('Finished analyzing file structure')
    # create the new directory structure
    logger.info('Starting reorganization')
    if len(filestruct['other']) > 0:
        if not os.path.exists(os.path.join(source, 'other')):
            os.makedirs(os.path.join(source, 'other'))
        if not os.path.exists(os.path.join(source, 'dicoms')):
            os.makedirs(os.path.join(source, 'dicoms'))
        for f in filestruct['other']:
            try:
                shutil.move(f, os.path.join(source, 'other'))
                counter.update()
            except shutil.Error as e:
                logger.debug(e)
        dicom_path = os.path.join(source, 'dicoms')
    else:
        dicom_path = source

    if len(filestruct['dicoms']['UNCATEGORIZED']) > 0:
        if not os.path.exists(os.path.join(dicom_path, 'UNCATEGORIZED')):
            os.makedirs(os.path.join(dicom_path, 'UNCATEGORIZED'))
        for f in filestruct['dicoms']['UNCATEGORIZED']:
            fname = os.path.basename(f)
            if not fname.endswith('.dcm'):
                fname += '.dcm'
            try:
                shutil.move(
                    f,
                    os.path.join(
                        dicom_path,
                        'UNCATEGORIZED/{}'.format(fname)))
                counter.update()
            except shutil.Error as e:
                logger.debug(e)
    for key in filestruct['dicoms'].keys():
        if key == 'UNCATEGORIZED':
            continue
        target_path = os.path.join(dicom_path, '/'.join(key))
        if not os.path.exists(target_path):
            os.makedirs(target_path)
        for f in filestruct['dicoms'][key]:
            fname = os.path.basename(f)
            if not fname.endswith('.dcm'):
                fname += '.dcm'
            try:
                shutil.move(f, os.path.join(target_path, fname))
                counter.update()
            except shutil.Error as e:
                logger.debug(e)
    # clean up empty directories
    logger.info('Finished moving files. Cleaning up empty subdirectories')
    remove_empty_subdirs(source)


def standardize_structure(source, dest):
    """
    Moves dicom files from a source directory in a recursive way and puts them in a structured form (
    patientid/studyid/seriesid/dicom.dcm) under a different destination directory. NOTE: This is not done in-place.

    :param source: The root directory containing the dicom files
    :param dest: The root directory where the dicom files will be put in a structured form
    """
    counter = FileCounter()
    if not os.path.exists(dest):
        os.makedirs(dest)
    dicoms_dest = os.path.join(dest, 'dicoms')
    logger.info('Started moving files')
    for r, c, f in os.walk(source):
        for filename in f:
            try:
                im = pydicom.dcmread(os.path.join(r, filename))
            except pydicom.errors.InvalidDicomError:
                target_dir = os.path.join(dest, 'other')
                if not os.path.exists(target_dir):
                    os.makedirs(target_dir)
                shutil.move(
                    os.path.join(
                        r, filename), os.path.join(
                        target_dir, filename))
                counter.update()
                continue
            try:
                pid = im.PatientID
                study = im.StudyInstanceUID
                series = im.SeriesInstanceUID
                target_dir = os.path.join(
                    dicoms_dest, '/'.join([pid, study, series]))
                if not filename.endswith('dcm'):
                    new_filename = filename + '.dcm'
                else:
                    new_filename = filename
                if not os.path.exists(target_dir):
                    os.makedirs(target_dir)
                shutil.move(
                    os.path.join(
                        r, filename), os.path.join(
                        target_dir, new_filename))
                counter.update()
            except KeyError:
                logging.warning(
                    'At least one of PatientID, StudyInstanceUID or SeriesInstanceUID is'
                    'missing in file {}'.format(
                        os.path.join(
                            r, filename)))
                target_dir = os.path.join(dicoms_dest, 'UNCATEGORIZED')
                if not os.path.exists(target_dir):
                    os.makedirs(target_dir)
                shutil.move(
                    os.path.join(
                        r, filename), os.path.join(
                        target_dir, new_filename))
                counter.update()
    logger.info('Finished moving files')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "source", help="the root directory containing dicom files")
    parser.add_argument("--output_dir", "-o",
                        help="name of the output directory")
    parser.add_argument(
        "--log",
        '-l',
        help="logging level to use: can be one of INFO, DEBUG, WARNING, ERROR, CRITICAL",
        choices=[
            'INFO',
            'DEBUG',
            'WARNING',
            'ERROR',
            'CRITICAL'],
        type=str.upper,
        default='WARNING')
    args = parser.parse_args()
    root = args.source
    loglevel = args.log
    numeric_level = getattr(logging, loglevel.upper(), None)
    logging.basicConfig(level=numeric_level)
    destination = args.output_dir
    logger = logging.getLogger('mover')
    if destination is not None:
        standardize_structure(root, destination)
    else:
        standardize_structure_in_place(root)
