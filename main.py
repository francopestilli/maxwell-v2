"""
app-maxwell-v2: Apply Maxwell filtering (SSS/tSSS) to Elekta/MEGIN MEG data.

Inputs : neuro/meg/fif (raw MEG)
Outputs: neuro/meg/fif (Maxwell-filtered raw MEG)

Calibration and cross-talk files are read from the input dataset if present,
otherwise the repo-bundled files are used automatically.
"""

import os
import sys

app_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(app_dir)
for search_path in [app_dir, parent_dir]:
    if os.path.isdir(os.path.join(search_path, 'brainlife_utils')):
        sys.path.insert(0, search_path)
        break

from brainlife_utils import (
    setup_matplotlib_backend,
    load_config,
    ensure_output_dirs,
    add_info_to_product,
    add_image_to_product,
    create_product_json,
)

setup_matplotlib_backend()
import matplotlib.pyplot as plt
import mne

# == SETUP ==
ensure_output_dirs('out_dir', 'out_figs', 'out_report')
report_items = []

# == LOAD CONFIG ==
config = load_config()

raw_file = config.get('fif') or config.get('mne') or config.get('meg') or None
if not raw_file or not os.path.isfile(raw_file):
    add_info_to_product(report_items, "FATAL: No MEG FIF file found. Set 'fif' in config.json.", "error")
    create_product_json(report_items)
    sys.exit(1)

# == PARAMETERS ==
def _to_none(val):
    if val is None or val == '' or val == 'None':
        return None
    return val

st_duration   = _to_none(config.get('param_st_duration'))
st_correlation = float(config.get('param_st_correlation', 0.98))
origin        = config.get('param_origin', 'auto')
int_order     = int(config.get('param_int_order', 8))
ext_order     = int(config.get('param_ext_order', 3))
coord_frame   = config.get('param_coord_frame', 'head')
regularize    = _to_none(config.get('param_regularize', 'in'))
mag_scale     = config.get('param_mag_scale', 100)
auto_bad_channels = str(config.get('auto_bad_channels', 'true')).lower() == 'true'

if st_duration is not None:
    st_duration = float(st_duration)
if mag_scale != 'auto':
    mag_scale = float(mag_scale)
if isinstance(origin, str) and origin != 'auto':
    origin = [float(x) for x in origin.split(',')]

# == CALIBRATION FILES ==
# Priority: input dataset files > repo-bundled files
calibration_file = _to_none(config.get('calibration'))
cross_talk_file  = _to_none(config.get('crosstalk'))

if calibration_file is None:
    bundled = os.path.join(app_dir, 'calibration_meg.dat')
    if os.path.exists(bundled):
        calibration_file = bundled
        add_info_to_product(report_items, "Using repo-bundled calibration file.", "info")

if cross_talk_file is None:
    bundled = os.path.join(app_dir, 'crosstalk_meg.fif')
    if os.path.exists(bundled):
        cross_talk_file = bundled
        add_info_to_product(report_items, "Using repo-bundled cross-talk file.", "info")

if calibration_file:
    add_info_to_product(report_items, f"Calibration: {os.path.basename(calibration_file)}", "good")
else:
    add_info_to_product(report_items, "No calibration file — SSS will run without fine calibration.", "warning")

if cross_talk_file:
    add_info_to_product(report_items, f"Cross-talk: {os.path.basename(cross_talk_file)}", "good")
else:
    add_info_to_product(report_items, "No cross-talk file.", "warning")

# == LOAD RAW ==
try:
    raw = mne.io.read_raw_fif(raw_file, allow_maxshield=True, preload=True, verbose=False)
except Exception as e:
    add_info_to_product(report_items, f"FATAL: Could not load MEG file: {e}", "error")
    create_product_json(report_items)
    sys.exit(1)

add_info_to_product(report_items, f"Loaded: {len(raw.ch_names)} channels, {raw.times[-1]:.1f}s", "info")

# Check Maxwell filter not already applied
if raw.info.get('proc_history'):
    sss_info  = raw.info['proc_history'][0]['max_info']['sss_info']
    tsss_info = raw.info['proc_history'][0]['max_info']['max_st']
    if bool(sss_info) or bool(tsss_info):
        add_info_to_product(report_items, "FATAL: Maxwell filtering already applied to this data.", "error")
        create_product_json(report_items)
        sys.exit(1)

# == AUTO BAD CHANNEL DETECTION ==
if auto_bad_channels:
    try:
        noisy_chs, flat_chs = mne.preprocessing.find_bad_channels_maxwell(
            raw,
            calibration=calibration_file,
            cross_talk=cross_talk_file,
            origin=origin,
            int_order=int_order,
            ext_order=ext_order,
            coord_frame=coord_frame,
            verbose=False,
        )
        raw.info['bads'] = list(set(raw.info['bads']) | set(noisy_chs) | set(flat_chs))
        add_info_to_product(
            report_items,
            f"Auto bad channels — noisy: {noisy_chs or 'none'}, flat: {flat_chs or 'none'}",
            "good" if not noisy_chs and not flat_chs else "warning",
        )
    except Exception as e:
        add_info_to_product(report_items, f"Bad channel detection failed (skipping): {e}", "warning")
else:
    if raw.info['bads']:
        add_info_to_product(report_items, f"Using pre-marked bad channels: {raw.info['bads']}", "info")
    else:
        add_info_to_product(report_items, "No bad channels marked.", "warning")

# == APPLY MAXWELL FILTER ==
try:
    raw_sss = mne.preprocessing.maxwell_filter(
        raw,
        calibration=calibration_file,
        cross_talk=cross_talk_file,
        origin=origin,
        int_order=int_order,
        ext_order=ext_order,
        st_duration=st_duration,
        st_correlation=st_correlation,
        coord_frame=coord_frame,
        regularize=regularize,
        mag_scale=mag_scale,
        verbose=True,
    )
except Exception as e:
    add_info_to_product(report_items, f"FATAL: Maxwell filtering failed: {e}", "error")
    create_product_json(report_items)
    sys.exit(1)

method = "tSSS" if st_duration else "SSS"
add_info_to_product(report_items, f"{method} applied successfully.", "good")

# == SAVE OUTPUT ==
out_fif = os.path.join('out_dir', 'raw.fif')
raw_sss.save(out_fif, overwrite=True)
add_info_to_product(report_items, f"Saved: {out_fif}", "info")

# == REPORT PLOTS ==
try:
    fig_before, axes = plt.subplots(2, 1, figsize=(12, 6))
    raw.pick('meg').plot_psd(fmax=100, ax=axes[0], show=False)
    axes[0].set_title('Before Maxwell filter')
    raw_sss.pick('meg').plot_psd(fmax=100, ax=axes[1], show=False)
    axes[1].set_title('After Maxwell filter')
    plt.tight_layout()
    psd_path = os.path.join('out_figs', 'psd_comparison.png')
    fig_before.savefig(psd_path, dpi=120)
    plt.close(fig_before)
    add_image_to_product(report_items, psd_path, "PSD before/after Maxwell filter")
except Exception as e:
    add_info_to_product(report_items, f"PSD plot failed (non-fatal): {e}", "warning")

create_product_json(report_items)
