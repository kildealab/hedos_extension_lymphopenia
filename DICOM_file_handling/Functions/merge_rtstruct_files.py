def merge_rtstruct_files(CT, RTSTRUCT_LOCATION, RTSTRUCTS):
    import os
    from rt_utils import RTStructMerger

    # Merge the first two RTSTRUCTs
    merged_rt_struct = RTStructMerger.merge_rtstructs(
        dicom_series_path=CT,
        rt_struct_path1=RTSTRUCTS[0],
        rt_struct_path2=RTSTRUCTS[1],
    )
    merged_rt_struct.save(os.path.join(RTSTRUCT_LOCATION, "segmentations.dcm"))

    RTSTRUCT = os.path.join(RTSTRUCT_LOCATION, "segmentations.dcm")
    merged_path = RTSTRUCTS[0]

    # Iteratively merge remaining RTSTRUCTs (if any)
    for path in RTSTRUCTS[1:]:
        merged = RTStructMerger.merge_rtstructs(
            dicom_series_path=CT,
            rt_struct_path1=merged_path,
            rt_struct_path2=path,
        )
        merged.save(RTSTRUCT)
        merged_path = RTSTRUCT

    print("[RTSTRUCT] Merged saved:", RTSTRUCT)
    return RTSTRUCT
