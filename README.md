# maxwell-v2

<!-- brainlife-app:begin (generated from the App manifest; edit the manifest, not this block) -->

> **Applies Maxwell filtering (SSS, or tSSS when a buffer duration is set) to Elekta/MEGIN MEG raw data with MNE-Python, with optional automatic noisy/flat channel detection, and outputs the filtered raw FIF.**

Loads the raw MEG file, optionally detects noisy and flat channels with find_bad_channels_maxwell, then runs mne.preprocessing.maxwell_filter with the given origin, temporal SSS settings and magnetometer scaling, writing the result and QC figures. Use it as an early MEG preprocessing step for MEGIN/Elekta data. Fine-calibration and cross-talk files are taken from the input when present; otherwise the calibration and cross-talk files bundled in the repository are used, which belong to a specific scanner and may not match yours. The App stops if the data were already Maxwell filtered.

| | |
|---|---|
| 📥 **Inputs** | `neuro/meeg/mne/raw` |
| 📤 **Outputs** | `neuro/meeg/mne/raw` |
| 🐳 **Container** | `brainlife/mne:1.2.1` |
| ⚙️ **Resources** | 1 CPUs · 12 GB memory · 2 h walltime |
| 🔗 **Run it** | [doi.org/10.25663/brainlife.app.930](https://doi.org/10.25663/brainlife.app.930) |

#### 📥 Inputs

| Input | Datatype | Required | Description |
|---|---|---|---|
| `mne` | `neuro/meeg/mne/raw` | yes | Raw MEG recording (Elekta/MEGIN FIF) not yet Maxwell filtered. |

#### 📤 Outputs

| Output | Datatype | Description |
|---|---|---|
| `out_dir` | `neuro/meeg/mne/raw` | Maxwell-filtered raw MEG data in FIF format. |

<details>
<summary><b>⚙️ Parameters</b> (5)</summary>

| Parameter | Type | Default | Description |
|---|---|---|---|
| `auto_bad_channels` | boolean | `true` | Detect noisy and flat channels with find_bad_channels_maxwell and mark them bad before filtering. The registered parameter id ends with a tab character while the code reads 'auto_bad_channels', so the default (true) is always used. |
| `param_st_duration` | number |  | Buffer length in seconds for temporal SSS (tSSS); empty for spatial SSS only. |
| `param_st_correlation` | number | `0.98` | Correlation limit between inner and outer subspaces used to reject components in tSSS. |
| `param_origin` | string | `auto` | Origin of the SSS expansion: 'auto' or comma-separated x,y,z coordinates. |
| `param_mag_scale` | number | `100` | Scaling applied to magnetometers relative to gradiometers (number or 'auto'). |

</details>

📚 **References used by this App:**
- Gramfort A. et al. MEG and EEG data analysis with MNE-Python. Frontiers in Neuroscience 7:267 (2013). [doi:10.3389/fnins.2013.00267](https://doi.org/10.3389/fnins.2013.00267)

<!-- brainlife-app:end -->

