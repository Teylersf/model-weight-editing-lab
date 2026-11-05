# Weight Lab Live

This local browser page follows a token trace as the model runs. The rainbow signal shows cumulative progress, with a separate decode-rate lane when the log has real timing. Use the Full, 128, or 48 sample windows and inspect a point with the pointer or arrow keys. Capture logs without timestamps use sample order. A token cap and a natural end token are reported separately. Pausing freezes the browser display while the model keeps running, and polling stops while the tab is hidden.

From the repository root, start the viewer with Python 3.11 or newer:

```powershell
python prototypes/trace-viewer/trace_viewer.py --workspace "C:\path\to\research"
```

Open http://127.0.0.1:8769/ on the machine running the viewer. The server listens on loopback. It looks under the selected workspace's `runs` directory for `native.log`, `native-stderr.log`, or `native.stderr.log` one to three subdirectories down, plus the nested ordinary evaluation groups and the three archived physical replay logs. Redirect the native runner's stderr to one of those files and keep live logging enabled. The viewer reads up to 1 MiB of structured `WR_LIVE` or `WR_HEAD` events and plots up to 640 representative samples. Run and case names are visible on this local page. Token text, prompts, and checkpoint data are excluded from the trace response.

To display your own tensor comparison, place a `weight-change.json` beside the Python file. Use an `id` unique to each comparison, a short `label`, and the numeric `relative_percent` for the Frobenius norm of the difference divided by the reference norm and multiplied by 100. Set `rows` and `columns` to the number of heatmap cells in each direction. Provide one numeric `rms` entry per cell, in row-major order, calculated from the saved weight differences in that region. Brighter cells represent larger RMS differences within that comparison. The heatmap describes the saved edit. The token trace describes a particular run.

Add comparisons as `weight-change-*.json` with different IDs. The tensor map loads the selected comparison on demand and draws the measured cells on one canvas. Hover to inspect a cell's RMS. A 128 × 256 map of the 5,120 × 17,408 D63 matrix measures 40 × 68 weights per cell. The full matrices stay on disk and the ordinary live polls carry comparison metadata only.
