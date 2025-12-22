import torch

import pydicom
import multiprocessing as mp
import os


def run_totalseg(CT, RTSTRUCT,task,fast, organs = None,):
    from totalsegmentator.python_api import totalsegmentator
    #organ_text_list = os.path.join(os.path.dirname(os.path.abspath(__file__)), "total_segmentator_organs.txt")

    #Running Contouring Algorithm
    totalsegmentator(
        input = CT,
        output = RTSTRUCT + "/" + task,
        task = task, # no subtask in this case
        roi_subset=organs if organs else None, #contour selected organs
        output_type = "dicom", #Use RTSTRUCT as output to input into HEDOS
        fast = fast, #fast algorithm version, less precise
        device = "mps" if torch.backends.mps.is_available() else "cpu" #using mps as GPU instead of CPU for faster simulation
    )
    print("Segmentation done")



