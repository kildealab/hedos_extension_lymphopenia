from dicompylercore import dicomparser, dvhcalc
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import pydicom
import numpy as np

# quick plotting script for the report (DVHs + blood dose figs)
# not meant to be a clean “library” thing — just makes the figures I needed.

# 1) File paths (DVH) and blood dose arrays (NPZ)
# NOTE: replace "..." with your local paths (I kept them out of git on purpose)
RS_LymphoTEC = "..."
RD_LymphoTEC = "..."

RS_MUHC = "..."
RD_MUHC = "..."

NPZ_LYMPHOTEC = "..."
NPZ_MUHC      = "..."


# 2) Helpers (DVH)
def get_roi_number(rs_path, roi_name):
    """
    Names are specified to plot organs, and so this helper function extracts the respective roi number.
    (dicompyler wants the ROI number, not the name)
    """
    structures = dicomparser.DicomParser(rs_path).GetStructures()
    name_to_number = {info["name"]: number for number, info in structures.items()}
    return name_to_number[roi_name]


def plot_dvh_for_roi(ax, rs_muhc, rd_muhc, rs_lymphotec, rd_lymphotec, roi_name):
    """
    Plot MUHC vs LymphoTEC DVHs for one ROI on one axis.
    Also drops a few manual "objective" markers just as a visual reminder of constraints.
    """
    dvh_muhc  = dvhcalc.get_dvh(rs_muhc,      rd_muhc,      get_roi_number(rs_muhc, roi_name))
    dvh_lymph = dvhcalc.get_dvh(rs_lymphotec, rd_lymphotec, get_roi_number(rs_lymphotec, roi_name))

    # Convert DVH counts to % volume (so all organs compare nicely)
    y_muhc  = 100 * dvh_muhc.counts  / dvh_muhc.counts[0]
    y_lymph = 100 * dvh_lymph.counts / dvh_lymph.counts[0]

    ax.plot(dvh_muhc.bincenters,  y_muhc,  label="MUHC Plan",              linewidth=2)
    ax.plot(dvh_lymph.bincenters, y_lymph, label="LymphoTEC-Optimized Plan", linewidth=2)

    ax.set_title(roi_name.replace("_", " ").title(), fontsize=12)
    ax.grid(True, alpha=0.6)

    # manual objective markers (I hard-coded these since it’s just for this report)
    roi_key = roi_name.lower()

    if roi_key == "lung":
        ax.scatter([5, 10], [45, 30], marker="v", color="tab:orange", s=40, zorder=5)  # LymphoTEC
        ax.scatter([20], [30], marker="v", color="tab:blue",   s=40, zorder=5)         # MUHC

    if roi_key == "esophagus":
        ax.scatter([60], [33], marker="v", color="tab:blue", s=40, zorder=5)           # MUHC

    if roi_key == "heart":
        ax.scatter([5, 10], [38, 25], marker="v", color="tab:orange", s=40, zorder=5)  # LymphoTEC
        ax.scatter([60, 35], [33, 50], marker="v", color="tab:blue",  s=40, zorder=5)  # MUHC

    if roi_key == "aorta":
        ax.scatter([5], [90], marker="v", color="tab:orange", s=40, zorder=5)          # LymphoTEC


# 3) DVH multiplot figure
# 2x3 grid to match the layout in the report
fig, axs = plt.subplots(2, 3, figsize=(11, 8), sharex=True, sharey=True)

rois = ["tumor", "heart", "lung", "aorta", "pulmonary_vein", "esophagus"]

for ax, roi in zip(axs.flat, rois):
    plot_dvh_for_roi(ax, RS_MUHC, RD_MUHC, RS_LymphoTEC, RD_LymphoTEC, roi)

# panel labels bottom-left (so they don’t hide the DVH curves)
panel_labels = ["(a)", "(b)", "(c)", "(d)", "(e)", "(f)"]
for i, ax in enumerate(axs.flat):
    ax.text(
        0.03, 0.05, panel_labels[i],
        transform=ax.transAxes,
        fontsize=13,
        fontweight="bold",
        va="bottom",
        ha="left",
    )

fig.supxlabel("Dose [Gy]", fontsize=12)
fig.supylabel("Volume [%]", fontsize=12)

# Legend: DVH curves + objective markers
handles, labels = axs[0, 0].get_legend_handles_labels()
handles += [
    Line2D([], [], linestyle="None", marker="v", color="tab:blue",   markersize=8, label="MUHC Ex. Objectives"),
    Line2D([], [], linestyle="None", marker="v", color="tab:orange", markersize=8, label="LymphoTEC Ex. Objectives"),
]
fig.legend(handles, [h.get_label() for h in handles],
           loc="upper center", ncol=4, frameon=False, fontsize=12)

plt.tight_layout(rect=[0, 0, 1, 0.95])

# Save both: PDF for paper, PNG for quick viewing
fig.savefig("dvh_comparison.pdf", bbox_inches="tight")
fig.savefig("dvh_comparison.png", dpi=300, bbox_inches="tight")
plt.show()


# 4) Tumor stats printing
RX = 60.0  # prescription dose (Gy)

def print_stats(label, RS, RD):
    # Quick sanity check: global 3D max from the RTDOSE grid
    ds = pydicom.dcmread(RD)
    dose = ds.pixel_array * ds.DoseGridScaling
    dmax_3d = dose.max()

    # Tumor stats from the DVH (this is what I actually report)
    dvh = dvhcalc.get_dvh(RS, RD, get_roi_number(RS, "tumor"))

    print("\n" + label)
    print(f"3D Dose MAX: {100*dmax_3d/RX:.1f} %")
    print(f"3D MAX for tumor: {100*dvh.max/RX:.1f} %")
    print(f"3D MIN for tumor: {100*dvh.min/RX:.1f} %")
    print(f"3D MEAN for tumor: {100*dvh.mean/RX:.1f} %")

print_stats("MUHC Plan", RS_MUHC, RD_MUHC)
print_stats("LymphoTEC Plan", RS_LymphoTEC, RD_LymphoTEC)


# 5) Blood dose figures (NPZ)
# These NPZ files come from the HEDOS simulation outputs (already aggregated).

# Output names (fixed, so I don't keep renaming files in LaTeX)
OUT_HIST_PDF     = "fig_blood_dose_histogram.pdf"
OUT_HIST_PNG     = "fig_blood_dose_histogram.png"
OUT_CONTRIB_PDF  = "fig_blood_dose_contributions.pdf"
OUT_CONTRIB_PNG  = "fig_blood_dose_contributions.png"

# LOAD
lym = np.load(NPZ_LYMPHOTEC, allow_pickle=True)
muh = np.load(NPZ_MUHC, allow_pickle=True)

blood_lym = lym["blood_dose"]
blood_muh = muh["blood_dose"]

mean_lym = float(lym["blood_mean"])
mean_muh = float(muh["blood_mean"])

bins_left  = lym["bins_left"]
xlim_left  = lym["xlim_left"]

bins_right = lym["bins_right"]
xlim_right = lym["xlim_right"]

# Organ order here is just what I cared about in the discussion
organs_to_show = [
    "heart",
    "lung",
    "aorta",
    "large_veins",
]

# key aliasing because sometimes I spelled oesophagus/esophagus differently in older runs…
def dose_key(data, organ):
    key = f"dose_{organ}"
    if key in data:
        return key
    if organ == "oesophagus" and "dose_esophagus" in data:
        return "dose_esophagus"
    if organ == "esophagus" and "dose_oesophagus" in data:
        return "dose_oesophagus"
    return None

# helper: add panel labels in TOP-RIGHT (keeps them away from the y-axis)
def add_panel_label(ax, label):
    ax.text(
        0.97, 0.95, label,
        transform=ax.transAxes,
        ha="right", va="top",
        fontsize=14, fontweight="bold"
    )


# Figure 1 — Blood dose histogram (percent)
fig_hist, ax = plt.subplots(figsize=(7, 4))

# weights so each histogram sums to 100% (makes MUHC vs LymphoTEC comparable)
w_muh = np.ones_like(blood_muh, dtype=float) * (100.0 / len(blood_muh))
w_lym = np.ones_like(blood_lym, dtype=float) * (100.0 / len(blood_lym))

ax.hist(blood_muh, bins=bins_left, color="C0", alpha=0.55, label="MUHC",      weights=w_muh)
ax.hist(blood_lym, bins=bins_left, color="C1", alpha=0.55, label="LymphoTEC", weights=w_lym)

ax.axvline(mean_muh, color="C0", linewidth=2,
           label=f"MUHC mean – {mean_muh:.3f} Gy")
ax.axvline(mean_lym, color="C1", linewidth=2,
           label=f"LymphoTEC mean – {mean_lym:.3f} Gy")

ax.set_xlabel("Dose [Gy]")
ax.set_ylabel("Simulated particles [%]")
ax.set_xlim(0, 0.5)

ax.grid(True, which="major", linestyle="-", linewidth=1.0, color="0.85")
ax.set_axisbelow(True)
ax.legend(frameon=False)

fig_hist.tight_layout()
fig_hist.savefig(OUT_HIST_PDF, bbox_inches="tight")
fig_hist.savefig(OUT_HIST_PNG, dpi=600, bbox_inches="tight")
plt.show()


# Figure 2 — Global y-limit (fair comparison across organs)
global_max = 0.0
for organ in organs_to_show:
    k_lym = dose_key(lym, organ)
    k_muh = dose_key(muh, organ)

    if k_lym is not None:
        arr = lym[k_lym]
        counts, _ = np.histogram(arr, bins=bins_right)
        counts_pct = counts * 100.0 / len(arr)
        global_max = max(global_max, float(counts_pct.max()))

    if k_muh is not None:
        arr = muh[k_muh]
        counts, _ = np.histogram(arr, bins=bins_right)
        counts_pct = counts * 100.0 / len(arr)
        global_max = max(global_max, float(counts_pct.max()))

ylim_right = (0.0, global_max * 1.05)

# Figure 2 — Organ-wise blood dose contributions (percent)
fig, axes = plt.subplots(1, 4, figsize=(11.5, 4.5), sharex=True, sharey=True)
axes = np.atleast_1d(axes).flatten()

panel_labels = ["(a)", "(b)", "(c)", "(d)"]

for idx, ax in enumerate(axes):
    organ = organs_to_show[idx]
    k_muh = dose_key(muh, organ)
    k_lym = dose_key(lym, organ)

    if k_muh is not None:
        arr = muh[k_muh]
        w = np.ones_like(arr, dtype=float) * (100.0 / len(arr))
        ax.hist(arr, bins=bins_right, histtype="step", linewidth=1.8,
                color="C0", label="MUHC", weights=w)

    if k_lym is not None:
        arr = lym[k_lym]
        w = np.ones_like(arr, dtype=float) * (100.0 / len(arr))
        ax.hist(arr, bins=bins_right, histtype="step", linewidth=1.8,
                color="C1", label="LymphoTEC", weights=w)

    ax.set_title(organ.replace("_", " ").title(), fontsize=12)
    ax.set_xlim(*xlim_right)
    ax.set_ylim(*ylim_right)

    ax.grid(True, which="major", linestyle="-", linewidth=1.0, color="0.85")
    ax.set_axisbelow(True)

    add_panel_label(ax, panel_labels[idx])

# LEGEND + LABELS (dedupe labels because matplotlib repeats them)
handles, labels = [], []
for ax in axes:
    h, l = ax.get_legend_handles_labels()
    for hh, ll in zip(h, l):
        if ll not in labels:
            handles.append(hh)
            labels.append(ll)

fig.legend(handles, labels, loc="upper center", ncol=2, frameon=False, fontsize=12)

axes[0].set_ylabel("Simulated particles [%]", fontsize=12)
fig.supxlabel("Dose [Gy]", fontsize=12)

fig.tight_layout(rect=[0, 0, 1, 0.92])
fig.savefig(OUT_CONTRIB_PDF, bbox_inches="tight")
fig.savefig(OUT_CONTRIB_PNG, dpi=600, bbox_inches="tight")
plt.show()
