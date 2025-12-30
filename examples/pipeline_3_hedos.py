import matplotlib as plt
plt.use("QtAgg") #required for sliding window (interactive figure)
import numpy as np
import os
from workflows import BloodDoseFromFields
from DICOM_file_handling.Functions.simulation_classes import (
    Patient_parameters,
    Treatment_parameters,
    Simulation_parameters)


# Pipeline Step 3: run HEDOS (field-based and not DVH based) multiple times and save blood-dose arrays
#
# This script runs the BloodDoseFromFields workflow n_runs times for a chosen plan
# version (INITIAL vs OPTIMIZED). Each run produces a per-particle blood dose array
# The script saves:
# 1) each run as a separate .npy file (with an incrementing index), and
# 2) a stacked array containing all runs with shape (n_runs, Nparticles)

#Activate for repeated simulation: blocks the interactive window that blocks code when doing repeated measurements
#plt.show = lambda *a, **k: None  # avoid "blocking" plots during batch runs

if __name__ == "__main__":

    # Step 3.1: choose plan version and number of runs
    n_runs = 2  # number of HEDOS runs (Monte Carlo repetitions)

    # Choose one depending on the plan used in pipeline_2_choosing_plan:
    #Version = "INITIAL"
    Version = "OPTIMIZED"

    nr_fractions = 30

    # Step 3.2: define organs used by the HEDOS model for this simulation
    organs_hedos = [
        "brain", "heart", "lung", "liver", "spleen", "kidneys", "large_veins", "tumor",
        "red_marrow", "oesophagus", "aorta", "inferior_vena_cava", "stomach", "pancreas"
    ]

    # Step 3.3: set patient / simulation / treatment parameters
    patient_parameters = Patient_parameters(
        gender="M",
        tumor_site="lung",
        tumor_volume_fraction=0.06,
        relative_blood_density=1.0,
        relative_perfusion=1.0,
        organs=organs_hedos
    )

    simulation_parameters = Simulation_parameters(
        sample_size=20_000,
        nr_steps=3400,
        dt=0.05,
        weibull_shape=2,
        generate_new=True,
        random_walk=True,
        accumulate=False
    )

    treatment_parameters = Treatment_parameters(
        nr_fractions=nr_fractions,
        total_beam_on_time=140,
        start_times=[0, 90],
        beam_on_times=[70, 70]
    )

    # Step 3.4: run HEDOS multiple times and save outputs
    all_runs = []

    def get_next_filename(base_name, ext=".npy"):
        i = 1
        while True:
            fname = f"{base_name}_{i}{ext}"
            if not os.path.exists(fname):
                return fname
            i += 1

    for run_idx in range(n_runs):
        print(f"\n===== HEDOS {Version} run {run_idx + 1}/{n_runs} =====")

        blood_dose_array = BloodDoseFromFields.blood_dose_distribution(
            simulation_parameters, patient_parameters, treatment_parameters
        )

        print("mean_blood_dose:", float(np.mean(blood_dose_array)))
        print("Blood dose computation done")

        # Save per-run result ( incrementing index)
        per_run_filename = get_next_filename(f"blood_dose_array_{Version}")
        np.save(per_run_filename, blood_dose_array)
        print(f"Saved single-run array to: {per_run_filename}")

        all_runs.append(blood_dose_array)

    # Stack and save all runs in one file
    all_runs = np.stack(all_runs, axis=0)
    all_runs_filename = f"blood_dose_arrays_all_runs_{Version}.npy"
    np.save(all_runs_filename, all_runs)

    print(f"\nSaved all runs to: {all_runs_filename}")
    print("Stacked array shape:", all_runs.shape)
