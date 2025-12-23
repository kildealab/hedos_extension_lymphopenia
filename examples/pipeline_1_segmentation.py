from DICOM_file_handling.Functions.merge_rtstruct_files import merge_rtstruct_files
from DICOM_file_handling.Functions.total_segmentator import run_totalseg
from organs import ORG_SYSTEMS

# Pipeline Step 1: CT segmentation and merging of RTSTRUCT files
#This step is only required for initial segmentation. Once this step completed,
#replanning can begin from step 2

if __name__ == "__main__":

    # Step 1.1: specify CT path and RTSTRUCT output location
    RTSTRUCT_LOCATION = "..."
    CT = "..."


    # Step 1.2: TotalSegmentator — whole-body organs (excluding vertebrae body)
    organs = [
        organ
        for system in ORG_SYSTEMS.values()
        for organ in system
        if organ not in ["intervertebral_discs", "vertebrae_body"]]
    run_totalseg(CT=CT, RTSTRUCT=RTSTRUCT_LOCATION, task="total", fast=False, organs=organs)


    # Step 1.3: TotalSegmentator — vertebrae body
    run_totalseg(CT=CT, RTSTRUCT=RTSTRUCT_LOCATION, task="vertebrae_body", fast=False)
    print("[PIPELINE] Step 1: TotalSegmentator RTSTRUCTs generated")


    # Step 1.4: merge multiple RTSTRUCT files into a single RTSTRUCT
    RTSTRUCTS = [f"{RTSTRUCT_LOCATION}/total/segmentations.dcm", f"{RTSTRUCT_LOCATION}/vertebrae_body/segmentations.dcm"]


    RTSTRUCT = merge_rtstruct_files(CT, RTSTRUCT_LOCATION, RTSTRUCTS)
    print("[PIPELINE] Step 1: RTSTRUCT files merged")
