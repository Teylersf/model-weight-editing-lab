# Weight Lab Live

This local browser page follows a token trace as the model runs. It shows elapsed decode time, generated token count, native runtime events, and a separate heatmap of a saved tensor comparison. A token cap and an end token are reported separately. The pause button freezes the browser display while the model can keep running.

From the repository root, start the viewer with Python 3.11 or newer:

```powershell
python prototypes/trace-viewer/trace_viewer.py --workspace "C:\path\to\research"
```

Open http://127.0.0.1:8769/ on the machine running the viewer. The server listens on loopback. It looks under the selected workspace's `runs` directory for `native.log`, `native-stderr.log`, or `native.stderr.log` one to three subdirectories down. Redirect the native runner's stderr to one of those files and keep the runner's live logging enabled. The viewer reads a bounded tail of structured `WR_LIVE` or `WR_HEAD` events. Run and case names are visible on this local page. Token text, prompts, and checkpoint data are excluded from the trace response.

To display your own tensor comparison, place a `weight-change.json` beside the Python file. Use an `id` unique to each comparison, a short `label`, and the numeric `relative_percent` for the Frobenius norm of the difference divided by the reference norm and multiplied by 100. Set `rows` and `columns` to the number of heatmap cells in each direction. Provide one numeric `rms` entry per cell, in row-major order, calculated from the saved weight differences in that region. Brighter cells represent larger RMS differences within that comparison. The heatmap describes the saved edit. The token trace describes a particular run.

To add a second choice to the heatmap selector, place another comparison in weight-change-reference.json with a different ID.
