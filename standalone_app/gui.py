"""Direct standalone GUI for GeoMorphX."""

from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from geomorphx.api import compute_rrim, compute_rrim_batch
from geomorphx.benchmark import run_benchmark_batch, run_benchmark_suite

METHOD_DEFS = [
    {
        "key": "rrim_baseline",
        "name": "Red Relief Image Map Baseline",
        "help": "Combina relieve local y pendiente para una visualizacion base del relieve.",
    },
    {
        "key": "rrim_multiscale",
        "name": "Red Relief Image Map Multi Scale",
        "help": "Promedia la respuesta Red Relief Image Map en multiples escalas de ventana.",
    },
    {
        "key": "rrim_anisotropic",
        "name": "Red Relief Image Map Directional",
        "help": "Integra un componente direccional segun azimuth para resaltar orientacion del relieve.",
    },
    {
        "key": "rrim_anisotropic_multiscale",
        "name": "Red Relief Image Map Directional Multi Scale",
        "help": "Version direccional en multiples escalas para patrones orientados persistentes.",
    },
    {
        "key": "rrim_structural",
        "name": "Structural Tensor Relief Response",
        "help": "Usa coherencia y alineacion estructural para resaltar organizacion geomorfologica.",
    },
    {
        "key": "rrim_plus",
        "name": "Extended Red Relief Image Map",
        "help": "Fusiona baseline, componente direccional, rugosidad y estructura en una salida compuesta.",
    },
    {"key": "slope", "name": "Slope in Degrees", "help": "Calcula la pendiente en grados para cada pixel."},
    {"key": "aspect", "name": "Aspect in Degrees", "help": "Calcula la orientacion de ladera en grados (0 a 360)."},
    {"key": "hillshade", "name": "Hillshade", "help": "Genera sombreado topografico segun iluminacion y azimuth."},
    {
        "key": "curvature_profile",
        "name": "Profile Curvature",
        "help": "Curvatura en la direccion de maxima pendiente (aceleracion o frenado de flujo).",
    },
    {
        "key": "curvature_plan",
        "name": "Plan Curvature",
        "help": "Curvatura en planta (convergencia o divergencia lateral del flujo).",
    },
    {"key": "curvature_mean", "name": "Mean Curvature", "help": "Curvatura media de la superficie."},
    {"key": "tpi", "name": "Topographic Position Index", "help": "Diferencia entre elevacion local y media vecina."},
    {"key": "tri", "name": "Terrain Ruggedness Index", "help": "Mide variacion altimetrica local del terreno."},
    {
        "key": "wetness_proxy",
        "name": "Topographic Wetness Proxy",
        "help": "Indicador aproximado de humedad potencial basado en pendiente y relieve local.",
    },
]
METHOD_NAME_TO_KEY = {item["name"]: item["key"] for item in METHOD_DEFS}
METHOD_NAME_TO_HELP = {item["name"]: item["help"] for item in METHOD_DEFS}
METHOD_NAMES = [item["name"] for item in METHOD_DEFS]


class GeoMorphXGUI(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("GeoMorphX Standalone")
        self.geometry("900x680")

        self._build_ui()

    def _build_ui(self) -> None:
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=12, pady=12)

        self.compute_tab = ttk.Frame(notebook)
        self.compute_batch_tab = ttk.Frame(notebook)
        self.benchmark_tab = ttk.Frame(notebook)
        self.benchmark_batch_tab = ttk.Frame(notebook)

        notebook.add(self.compute_tab, text="Compute")
        notebook.add(self.compute_batch_tab, text="Compute Batch")
        notebook.add(self.benchmark_tab, text="Benchmark")
        notebook.add(self.benchmark_batch_tab, text="Benchmark Batch")

        self._build_compute_tab()
        self._build_compute_batch_tab()
        self._build_benchmark_tab()
        self._build_benchmark_batch_tab()

        log_frame = ttk.LabelFrame(self, text="Log")
        log_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.log_text = tk.Text(log_frame, height=10)
        self.log_text.pack(fill="both", expand=True, padx=8, pady=8)

    def _browse_file(self, target_var: tk.StringVar, save: bool = False) -> None:
        if save:
            path = filedialog.asksaveasfilename(defaultextension=".tif")
        else:
            path = filedialog.askopenfilename(filetypes=[("GeoTIFF", "*.tif *.tiff"), ("All files", "*.*")])
        if path:
            target_var.set(path)

    def _browse_dir(self, target_var: tk.StringVar) -> None:
        path = filedialog.askdirectory()
        if path:
            target_var.set(path)

    def _row_with_entry(self, parent: ttk.Frame, label: str, var: tk.StringVar, row: int, browse_kind: str | None = None) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=6, pady=6)
        ttk.Entry(parent, textvariable=var, width=70).grid(row=row, column=1, sticky="we", padx=6, pady=6)
        if browse_kind == "file_open":
            ttk.Button(parent, text="Browse", command=lambda: self._browse_file(var, save=False)).grid(row=row, column=2, padx=6, pady=6)
        elif browse_kind == "file_save":
            ttk.Button(parent, text="Browse", command=lambda: self._browse_file(var, save=True)).grid(row=row, column=2, padx=6, pady=6)
        elif browse_kind == "dir":
            ttk.Button(parent, text="Browse", command=lambda: self._browse_dir(var)).grid(row=row, column=2, padx=6, pady=6)

    def _build_common_method_controls(self, parent: ttk.Frame, start_row: int) -> dict[str, tk.Variable]:
        method_var = tk.StringVar(value=METHOD_NAMES[0])
        scales_var = tk.StringVar(value="5,15,45")
        window_var = tk.StringVar(value="9")
        azimuth_var = tk.StringVar(value="45")
        directional_weight_var = tk.StringVar(value="0.6")
        anisotropy_weight_var = tk.StringVar(value="0.3")
        roughness_weight_var = tk.StringVar(value="0.25")
        structural_weight_var = tk.StringVar(value="0.2")

        ttk.Label(parent, text="Method").grid(row=start_row, column=0, sticky="w", padx=6, pady=6)
        ttk.Combobox(parent, textvariable=method_var, values=METHOD_NAMES, state="readonly").grid(
            row=start_row, column=1, sticky="we", padx=6, pady=6
        )
        ttk.Button(
            parent,
            text="Help",
            command=lambda: messagebox.showinfo(
                "Method Help",
                f"{method_var.get()}\n\n{METHOD_NAME_TO_HELP.get(method_var.get(), 'No description available.')}",
            ),
        ).grid(row=start_row, column=2, padx=6, pady=6)

        for i, (label, var) in enumerate(
            [
                ("Scales", scales_var),
                ("Window", window_var),
                ("Azimuth", azimuth_var),
                ("Directional Weight", directional_weight_var),
                ("Anisotropy Weight", anisotropy_weight_var),
                ("Roughness Weight", roughness_weight_var),
                ("Structural Weight", structural_weight_var),
            ],
            start=1,
        ):
            ttk.Label(parent, text=label).grid(row=start_row + i, column=0, sticky="w", padx=6, pady=6)
            ttk.Entry(parent, textvariable=var).grid(row=start_row + i, column=1, sticky="we", padx=6, pady=6)

        return {
            "method": method_var,
            "scales": scales_var,
            "window": window_var,
            "azimuth": azimuth_var,
            "directional_weight": directional_weight_var,
            "anisotropy_weight": anisotropy_weight_var,
            "roughness_weight": roughness_weight_var,
            "structural_weight": structural_weight_var,
        }

    def _selected_method_key(self, method_display_name: str) -> str:
        return METHOD_NAME_TO_KEY[method_display_name]

    def _parse_scales(self, raw: str) -> list[int]:
        return [int(x.strip()) for x in raw.split(",") if x.strip()]

    def _parse_azimuth(self, raw: str) -> float | list[float]:
        parts = [float(x.strip()) for x in raw.split(",") if x.strip()]
        if len(parts) == 1:
            return parts[0]
        return parts

    def _append_log(self, text: str) -> None:
        self.log_text.insert("end", text + "\n")
        self.log_text.see("end")

    def _run_async(self, fn) -> None:
        def wrapped():
            try:
                fn()
            except Exception as exc:  # noqa: BLE001
                self.after(0, lambda: messagebox.showerror("GeoMorphX", str(exc)))
                self.after(0, lambda: self._append_log(f"ERROR: {exc}"))

        threading.Thread(target=wrapped, daemon=True).start()

    def _build_compute_tab(self) -> None:
        frame = self.compute_tab
        frame.columnconfigure(1, weight=1)

        dem_var = tk.StringVar()
        out_var = tk.StringVar()
        debug_var = tk.StringVar()

        self._row_with_entry(frame, "Input DEM", dem_var, 0, "file_open")
        self._row_with_entry(frame, "Output TIFF", out_var, 1, "file_save")
        self._row_with_entry(frame, "Debug Dir (optional)", debug_var, 2, "dir")
        controls = self._build_common_method_controls(frame, 3)

        def run_compute() -> None:
            result = compute_rrim(
                dem_path=dem_var.get(),
                out_path=out_var.get(),
                method=self._selected_method_key(controls["method"].get()),
                scales=self._parse_scales(controls["scales"].get()),
                window=int(controls["window"].get()),
                azimuth_deg=self._parse_azimuth(controls["azimuth"].get()),
                directional_weight=float(controls["directional_weight"].get()),
                anisotropy_weight=float(controls["anisotropy_weight"].get()),
                roughness_weight=float(controls["roughness_weight"].get()),
                structural_weight=float(controls["structural_weight"].get()),
                debug_dir=(debug_var.get() or None),
            )
            self.after(0, lambda: self._append_log(f"Compute OK: {result}"))

        ttk.Button(frame, text="Run Compute", command=lambda: self._run_async(run_compute)).grid(
            row=11, column=1, sticky="e", padx=6, pady=10
        )

    def _build_compute_batch_tab(self) -> None:
        frame = self.compute_batch_tab
        frame.columnconfigure(1, weight=1)

        dem_dir_var = tk.StringVar()
        out_dir_var = tk.StringVar()
        pattern_var = tk.StringVar(value="*")
        recursive_var = tk.BooleanVar(value=True)
        save_debug_var = tk.BooleanVar(value=False)

        self._row_with_entry(frame, "DEM Directory", dem_dir_var, 0, "dir")
        self._row_with_entry(frame, "Output Directory", out_dir_var, 1, "dir")
        ttk.Label(frame, text="Pattern").grid(row=2, column=0, sticky="w", padx=6, pady=6)
        ttk.Entry(frame, textvariable=pattern_var).grid(row=2, column=1, sticky="we", padx=6, pady=6)
        ttk.Checkbutton(frame, text="Recursive", variable=recursive_var).grid(row=2, column=2, sticky="w", padx=6, pady=6)
        ttk.Checkbutton(frame, text="Save Debug", variable=save_debug_var).grid(row=3, column=2, sticky="w", padx=6, pady=6)

        controls = self._build_common_method_controls(frame, 3)

        def run_compute_batch() -> None:
            outputs, manifest = compute_rrim_batch(
                dem_dir=dem_dir_var.get(),
                out_dir=out_dir_var.get(),
                method=self._selected_method_key(controls["method"].get()),
                pattern=pattern_var.get(),
                recursive=recursive_var.get(),
                scales=self._parse_scales(controls["scales"].get()),
                window=int(controls["window"].get()),
                azimuth_deg=self._parse_azimuth(controls["azimuth"].get()),
                directional_weight=float(controls["directional_weight"].get()),
                anisotropy_weight=float(controls["anisotropy_weight"].get()),
                roughness_weight=float(controls["roughness_weight"].get()),
                structural_weight=float(controls["structural_weight"].get()),
                save_debug=save_debug_var.get(),
            )
            self.after(0, lambda: self._append_log(f"Compute Batch OK: {len(outputs)} files, manifest={manifest}"))

        ttk.Button(frame, text="Run Compute Batch", command=lambda: self._run_async(run_compute_batch)).grid(
            row=11, column=1, sticky="e", padx=6, pady=10
        )

    def _build_benchmark_tab(self) -> None:
        frame = self.benchmark_tab
        frame.columnconfigure(1, weight=1)

        out_dir_var = tk.StringVar()
        dem_var = tk.StringVar()
        size_var = tk.StringVar(value="512")
        repeats_var = tk.StringVar(value="3")
        window_var = tk.StringVar(value="9")
        scales_var = tk.StringVar(value="5,15,45")
        azimuth_var = tk.StringVar(value="45")
        tile_size_var = tk.StringVar(value="0")

        self._row_with_entry(frame, "Output Directory", out_dir_var, 0, "dir")
        self._row_with_entry(frame, "Input DEM (optional)", dem_var, 1, "file_open")
        for i, (label, var) in enumerate(
            [
                ("Synthetic Size", size_var),
                ("Repeats", repeats_var),
                ("Window", window_var),
                ("Scales", scales_var),
                ("Azimuth", azimuth_var),
                ("Tile Size", tile_size_var),
            ],
            start=2,
        ):
            ttk.Label(frame, text=label).grid(row=i, column=0, sticky="w", padx=6, pady=6)
            ttk.Entry(frame, textvariable=var).grid(row=i, column=1, sticky="we", padx=6, pady=6)

        def run_benchmark() -> None:
            rows, csv_path, json_path, md_path, png_path = run_benchmark_suite(
                out_dir=out_dir_var.get(),
                dem_path=(dem_var.get() or None),
                size=int(size_var.get()),
                repeats=int(repeats_var.get()),
                scales=self._parse_scales(scales_var.get()),
                window=int(window_var.get()),
                azimuth_deg=self._parse_azimuth(azimuth_var.get()),
                tile_size=int(tile_size_var.get()),
            )
            self.after(
                0,
                lambda: self._append_log(
                    f"Benchmark OK: methods={len(rows)} csv={csv_path} json={json_path} md={md_path} png={png_path}"
                ),
            )

        ttk.Button(frame, text="Run Benchmark", command=lambda: self._run_async(run_benchmark)).grid(
            row=9, column=1, sticky="e", padx=6, pady=10
        )

    def _build_benchmark_batch_tab(self) -> None:
        frame = self.benchmark_batch_tab
        frame.columnconfigure(1, weight=1)

        dem_dir_var = tk.StringVar()
        out_dir_var = tk.StringVar()
        pattern_var = tk.StringVar(value="*")
        recursive_var = tk.BooleanVar(value=True)
        repeats_var = tk.StringVar(value="3")
        window_var = tk.StringVar(value="9")
        scales_var = tk.StringVar(value="5,15,45")
        azimuth_var = tk.StringVar(value="45")
        tile_size_var = tk.StringVar(value="0")

        self._row_with_entry(frame, "DEM Directory", dem_dir_var, 0, "dir")
        self._row_with_entry(frame, "Output Directory", out_dir_var, 1, "dir")
        ttk.Label(frame, text="Pattern").grid(row=2, column=0, sticky="w", padx=6, pady=6)
        ttk.Entry(frame, textvariable=pattern_var).grid(row=2, column=1, sticky="we", padx=6, pady=6)
        ttk.Checkbutton(frame, text="Recursive", variable=recursive_var).grid(row=2, column=2, sticky="w", padx=6, pady=6)

        for i, (label, var) in enumerate(
            [
                ("Repeats", repeats_var),
                ("Window", window_var),
                ("Scales", scales_var),
                ("Azimuth", azimuth_var),
                ("Tile Size", tile_size_var),
            ],
            start=3,
        ):
            ttk.Label(frame, text=label).grid(row=i, column=0, sticky="w", padx=6, pady=6)
            ttk.Entry(frame, textvariable=var).grid(row=i, column=1, sticky="we", padx=6, pady=6)

        def run_benchmark_batch() -> None:
            rows, summary_csv, summary_json, summary_md = run_benchmark_batch(
                dem_dir=dem_dir_var.get(),
                out_dir=out_dir_var.get(),
                pattern=pattern_var.get(),
                recursive=recursive_var.get(),
                repeats=int(repeats_var.get()),
                scales=self._parse_scales(scales_var.get()),
                window=int(window_var.get()),
                azimuth_deg=self._parse_azimuth(azimuth_var.get()),
                tile_size=int(tile_size_var.get()),
            )
            self.after(
                0,
                lambda: self._append_log(
                    f"Benchmark Batch OK: inputs={len(rows)} csv={summary_csv} json={summary_json} md={summary_md}"
                ),
            )

        ttk.Button(frame, text="Run Benchmark Batch", command=lambda: self._run_async(run_benchmark_batch)).grid(
            row=9, column=1, sticky="e", padx=6, pady=10
        )


def main() -> int:
    app = GeoMorphXGUI()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
