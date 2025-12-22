import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import ttest_rel

# 4.1 — Parameters and inputs
DAYS = 41
NFX = 30
DAY = 40
ALC0 = 1.0

MU, MU_SD = 2.18, 0.35
SF, SF_SD = 0.57, 0.05
SREC = 0.02
Z = 1.96

A = np.load("blood_dose_arrays_all_runs_Initial.npy")
B = np.load("blood_dose_arrays_all_runs_Optimized.npy")

n = A.shape[0]
days = np.arange(DAYS + 1)

# 4.2 — ALC and survival models
def surv(D, mu, sf):
    return sf ** (1 - np.exp(-mu * D))

def alc_curve(K):
    alc = [ALC0]
    fx = 0
    for d in range(1, DAYS + 1):
        v = alc[-1]
        if fx < NFX and (d - 1) % 7 < 5:
            v *= K
            fx += 1
        v += (ALC0 - v) * (1 - np.exp(-SREC))
        alc.append(v)
    return np.array(alc)

def alc_from_mean(D, mu, sf):
    return alc_curve(surv(D, mu, sf).mean())

# 4.3 — ALC simulation (per run)
ALC_A = np.zeros((n, DAYS + 1))
ALC_B = np.zeros_like(ALC_A)

for i in range(n):
    ALC_A[i] = alc_from_mean(A[i], MU, SF)
    ALC_B[i] = alc_from_mean(B[i], MU, SF)

# 4.4 — Paired statistical tests
A40 = ALC_A[:, DAY]
B40 = ALC_B[:, DAY]

drop40_A = ALC0 - A40
drop40_B = ALC0 - B40
t_drop, p_drop = ttest_rel(drop40_B, drop40_A)

early = slice(0, 15)
dropA = ALC0 - ALC_A[:, early].min(1)
dropB = ALC0 - ALC_B[:, early].min(1)
t_nad, p_nad = ttest_rel(dropB, dropA)

# 4.5 — Statistical uncertainty across runs
meanA = ALC_A.mean(0)
meanB = ALC_B.mean(0)

semA = ALC_A.std(0, ddof=1) / np.sqrt(n)
semB = ALC_B.std(0, ddof=1) / np.sqrt(n)

DIFF = ALC_B - ALC_A
meanD = DIFF.mean(0)
semD = DIFF.std(0, ddof=1) / np.sqrt(n)

# 4.6 — Biological uncertainty propagation
DA = A.mean(0)
DB = B.mean(0)

def sens(D):
    mu_hi = alc_from_mean(D, MU + MU_SD, SF)
    mu_lo = alc_from_mean(D, MU - MU_SD, SF)
    sf_hi = alc_from_mean(D, MU, SF + SF_SD)
    sf_lo = alc_from_mean(D, MU, SF - SF_SD)
    return (
        (mu_hi - mu_lo) / (2 * MU_SD),
        (sf_hi - sf_lo) / (2 * SF_SD),
        mu_hi, mu_lo, sf_hi, sf_lo
    )

dA_mu, dA_sf, A_mhi, A_mlo, A_shi, A_slo = sens(DA)
dB_mu, dB_sf, B_mhi, B_mlo, B_shi, B_slo = sens(DB)

bioA = np.sqrt((dA_mu * MU_SD)**2 + (dA_sf * SF_SD)**2)
bioB = np.sqrt((dB_mu * MU_SD)**2 + (dB_sf * SF_SD)**2)

dD_mu = ((B_mhi - A_mhi) - (B_mlo - A_mlo)) / (2 * MU_SD)
dD_sf = ((B_shi - A_shi) - (B_slo - A_slo)) / (2 * SF_SD)
bioD = np.sqrt((dD_mu * MU_SD)**2 + (dD_sf * SF_SD)**2)

# 4.7 — Total uncertainty and scaling
errA = Z * np.sqrt(semA**2 + bioA**2)
errB = Z * np.sqrt(semB**2 + bioB**2)
errD = Z * np.sqrt(semD**2 + bioD**2)

A_m = 100 * meanA
B_m = 100 * meanB
D_m = 100 * meanD

A_e = 100 * errA
B_e = 100 * errB
D_e = 100 * errD

# 4.8 — ΔALC metrics
mean40 = meanD[DAY]
ci40 = errD[DAY]

early_window = meanD[:15]
early_err = errD[:15]

early_day = np.argmax(early_window)
early_mean = early_window[early_day]
early_ci = early_err[early_day]

# 4.9 — Visualization
fig, (ax1, ax2) = plt.subplots(
    2, 1, sharex=True, figsize=(12, 8),
    gridspec_kw={"height_ratios": [5, 2]}
)

# MUHC — blue
ax1.plot(days, A_m, color="tab:blue", label="MUHC Constraints")
ax1.fill_between(days, A_m - A_e, A_m + A_e,
                 color="tab:blue", alpha=0.2)

# LymphoTEC — orange
ax1.plot(days, B_m, color="tab:orange", label="MUHC + LymphoTEC Guidelines")
ax1.fill_between(days, B_m - B_e, B_m + B_e,
                 color="tab:orange", alpha=0.2)

ax1.set_ylabel("ALC [% baseline]")
ax1.grid(alpha=0.3)
ax1.legend()
ax1.text(0.02, 0.98, "a)", transform=ax1.transAxes,
         fontsize=16, fontweight="bold", va="top")

# ΔALC — black / gray
ax2.plot(days, D_m, color="black", label="ΔALC")
ax2.fill_between(days, D_m - D_e, D_m + D_e,
                 color="lightgray", alpha=0.4)
ax2.axhline(0, color="black")

ax2.set_xlabel("Time [days]")
ax2.set_ylabel("ΔALC [%]")
ax2.grid(alpha=0.3)
ax2.legend()
ax2.text(0.02, 0.98, "b)", transform=ax2.transAxes,
         fontsize=16, fontweight="bold", va="top")

plt.tight_layout()
plt.show()

# 4.10 — Key statistical results

print("\nPaired comparisons (optimized vs initial):")
print(f" End of treatment (day {DAY}): p = {p_drop:.3e}")
print(f" Early nadir (days 0–14): p = {p_nad:.3e}")

print("\nAbsolute lymphocyte sparing (ΔALC):")
print(
    f" Maximum early sparing at day {early_day}: "
    f"{early_mean*100:.2f}% "
    f"(95% CI {((early_mean-early_ci)*100):.2f}–{((early_mean+early_ci)*100):.2f}%)"
)
print(
    f" End of treatment (day {DAY}): "
    f"{mean40*100:.2f}% "
    f"(95% CI {((mean40-ci40)*100):.2f}–{((mean40+ci40)*100):.2f}%)"
)

# 4.11 — Mean blood dose per fraction

mean_dose_A = A.mean(axis=1)
mean_dose_B = B.mean(axis=1)

mean_A = mean_dose_A.mean()
mean_B = mean_dose_B.mean()

sem_A = mean_dose_A.std(ddof=1) / np.sqrt(n)
sem_B = mean_dose_B.std(ddof=1) / np.sqrt(n)

print("\nMean blood dose per fraction:")
print(f" Initial plan: {mean_A:.4f} Gy ± {sem_A:.4f} Gy (SEM)")
print(f" Optimized plan: {mean_B:.4f} Gy ± {sem_B:.4f} Gy (SEM)")
