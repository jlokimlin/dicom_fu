# dicom_fu
Contains code for all things dicom

## dicom_exploration.py
This script is useful for summarizing metadata from dicom files. Assuming proper directory structure: patients/Studies/Series/dicom_files (mainly assumes all dicom files are in the leaf nodes) it looks for CT or MR files (at present only CT and MR are implemented), reads the dicom headers using pydicom and collects the desired fields in desired format.  
#### Usage: 
You can use the functions separately or as a script. To use as a script: 

**./dicom_exploration.py ROOT -o OUTPUT_FILE**

where ROOT (required argument) is the root directory containing the dicom files (the code recurses through subdirectories), and OUTPUT_FILE is the name of the output file (.csv) - this argument is optional, by default it is summary.csv.
#### Requires:
  - autopep8==1.4.3,
  - cycler==0.10.0,
  - kiwisolver==1.0.1,
  - matplotlib==3.0.2, 
  - numpy==1.16.0
  - pandas==0.24.1
  - pycodestyle==2.4.0
  - pydicom==1.2.2
  - pyparsing==2.3.1
  - python-dateutil==2.7.5
  - pytz==2018.9
  - scikit-learn==0.20.2
  - scipy==1.2.0
  - six==1.12.0
  - tqdm==4.31.1
