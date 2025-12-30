import os
from DICOM_file_handling.Functions import dicom_conversion
from DICOM_file_handling.Functions.merge_roi_groups import merge_rtstruct
from organs import GROUPS

# Pipeline Step 2: plan selection and NumPy conversion
#
# Because HEDOS can only store one RD file at a time (and its corresponding CT and RS),
# this script selects a specific treatment plan and converts the corresponding DICOM
# inputs into NumPy format. Structures in the RTSTRUCT are first grouped into predefined
# anatomical categories, then the grouped RTSTRUCT + CT + RTDOSE are converted for HEDOS.
#
# Note: Collapsed polygons (warnings shown once when written and once when saved)
# correspond to structures below the minimum area threshold and are discarded automatically
# (see project report for full details).
#
# Important: the RTSTRUCT used here must include a "tumor" ROI. Since the tumor is not
# produced by the automatic segmentation, it must be added externally.

if __name__ == "__main__":

    # Step 2.1: specify the plan DICOM paths (CT, RTSTRUCT, RTDOSE)

    ####### MUHC #########
    # RTDOSE = "/Users/charles-etiennegaudet/Downloads/Phantom_Charles/half_arc_2/RD.1.2.246.352.71.7.991924009032.4305404.20251127193956.dcm"
    # CT = "/Users/charles-etiennegaudet/Downloads/Phantom_Charles/half_arc_2/MUHC_CT"
    # RTSTRUCT = "/Users/charles-etiennegaudet/Downloads/Phantom_Charles/half_arc_2/RS.1.2.246.352.71.4.991924009032.744827.20251127193149.dcm"

    ####### LymphoTEC #########
    RTDOSE = "/Users/charles-etiennegaudet/Downloads/Lymphopenia_LymphotecConst2/RD.1.2.246.352.221.5103741333306566415.4719648016124851644.dcm"
    CT = "/Users/charles-etiennegaudet/Downloads/Lymphopenia_LymphotecConst2/Lymph_ct"
    RTSTRUCT = "/Users/charles-etiennegaudet/Downloads/Lymphopenia_LymphotecConst2/RS.1.2.246.352.221.5689110468242748410.18302259186374122660.dcm"

    # Step 2.2: group structures by merging ROIs (masks) inside the RTSTRUCT (GROUPS in organs.py)
    groups = GROUPS
    grouped_rtstruct_location = os.path.join(os.path.dirname(RTSTRUCT), "segmentations_grouped.dcm")

    merge_rtstruct(RTSTRUCT, CT, grouped_rtstruct_location, groups=groups)
    print("[PIPELINE] Step 2: Grouped RTSTRUCT saved:", grouped_rtstruct_location)

    # Step 2.3: convert grouped RTSTRUCT + CT + RTDOSE to NumPy
    dicom_conversion(CT, grouped_rtstruct_location, RTDOSE)
    print("[PIPELINE] Step 2: NumPy inputs ready")
