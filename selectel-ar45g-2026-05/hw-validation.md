# Selectel AR45G — hardware validation

Independently measured for the ЛИИ × Selectel pilot (PRD S4). Read-only baseline + isolated
stress/stability soaks, run via Ansible (`capture_gpu_baseline.yml` + `gpu_stress_validation.yml`,
`--limit`-guarded, results fetched back). Raw logs retained privately.

Measured **2026-05-24** · Ubuntu 24.04 LTS (kernel 6.17) · NVIDIA driver 595.71.05 / CUDA 13.2.

## Hardware

| Component | Spec |
|---|---|
| GPU | 1× NVIDIA RTX PRO 6000 Blackwell **Server Edition**, 96 GB GDDR7 (SM_120) |
| CPU | AMD Ryzen 9 9950X — 16 cores / 32 threads |
| RAM | 192 GB DDR5 (non-ECC) |
| Storage | 2× Samsung SSD 990 PRO 2 TB M.2 (software MD-RAID-1, ext4) |
| PCIe | Gen5 (32 GT/s) ×16 to the GPU |
| Network | 1 GbE |
| OS | Ubuntu 24.04 LTS |

> Two things worth knowing up front: the GPU is the **"Server Edition"** SKU (passive/data-center
> cooling, not the active-cooled Workstation card), and the system NVMe are **consumer** Samsung
> 990 PRO M.2 — which matters for the thermal finding below.

## Stability + stress results

| Test | Duration | Result |
|---|---|---|
| **GPU thermal burn** | 30 min @ ~600 W | ✅ **No thermal throttle.** ~74 °C sustained; HW/SW thermal slowdown counters = 0. Only ~182 ms of SW power-capping across the whole run. |
| **NVMe sustained write** | 1 h randwrite / drive | ✅ **No throttle.** Both drives held ~**860 K** 4K-randwrite IOPS for the full hour. |
| **CPU + RAM** | 15 min, 32 threads | ✅ 0 errors; memory bandwidth ~21.3 GB/s. |
| **PCIe link** | sampled under GPU load | ✅ **Gen5 ×16 confirmed under load** (idle ASPM downclocks the link to Gen1 — measure under load). |
| **Host↔device bandwidth** | nvbandwidth v0.9 | H2D **44.8 GB/s** · D2H **42.0 GB/s** |
| **Network** | mtr → 8.8.8.8 | ~4 ms, 0 % loss |

Governor was set to `performance` for honest measurement (the box ships in `powersave`).

## Honest finding — NVMe thermal asymmetry

The two M.2 slots behave very differently under sustained writes:

| Drive | Temp range (1 h soak) | Write IOPS |
|---|---|---:|
| nvme0 | 36–42 °C | ~856 K |
| nvme1 | **65–76 °C** | ~861 K |

nvme1 runs **~33 °C hotter** and peaked **76 °C** — a chassis-airflow / M.2-slot-placement effect
typical of consumer 990 PRO drives on a dense board. It **did not throttle** within the hour
(IOPS held within noise of the cooler drive), but it's the component to watch under longer or
hotter sustained-write workloads (e.g. heavy training-checkpoint bursts). Flagged to Selectel.

## Verdict

Clean bill of health for SFT/serving: the GPU sustains full power without thermal throttle, the
NVMe array sustains ~860 K random-write IOPS without throttle, and the PCIe link runs full Gen5 ×16
under load. The single watch-item is nvme1's running temperature, not its performance.

## Reproduce

`capture_gpu_baseline.yml` (A.1, read-only) + `gpu_stress_validation.yml` (A.2–A.6), both
`--limit <host>` in the csylabs Ansible inventory. A combined full-system soak (`gpu_combined_soak.yml`,
A.7) runs in Phase C alongside the real training/serving load.
