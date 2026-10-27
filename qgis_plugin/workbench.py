"""Dockable DEM product workflow, inspired by TerraWorkbench's panel structure."""
from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import uuid
import weakref

from qgis.PyQt import sip
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor, QIcon
from qgis.PyQt.QtWidgets import (
    QComboBox, QDockWidget, QDoubleSpinBox, QFileDialog, QFormLayout,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMessageBox, QProgressBar, QPushButton, QScrollArea, QSpinBox, QTabWidget,
    QTextBrowser, QVBoxLayout, QWidget,
)
from qgis.core import (
    QgsApplication, QgsMapLayerProxyModel, QgsProject, QgsRasterLayer,
    QgsSettings, QgsTask, QgsPalettedRasterRenderer,
)
from qgis.gui import QgsMapLayerComboBox

from .suite_imports import ensure_suite_importable

ensure_suite_importable()
from geomorphx.methods import METHODS
from geomorphx.recipes import (
    create_recipe, execute_recipe, normalize_recipe,
    load_recipe as load_recipe_file, save_recipe as save_recipe_file,
)

PREFIX = "geomorphx_rrim_suite:"
HYDROLOGY = {"fill_depressions", "flow_accumulation_d8", "twi_d8", "flow_direction_d8",
             "drainage_basins_d8", "flow_length_d8", "flow_accumulation_mfd", "twi_mfd"}


def method_label(method):
    return method.replace("rrim", "RRIM").replace("tpi", "TPI").replace("tri", "TRI").replace("_", " ")


def validate_recipe(data):
    """Compatibility wrapper for the shared, frontend-independent validator."""
    return normalize_recipe(data)["products"]


class ProductTask(QgsTask):
    def __init__(self, source, output_root, products, receiver, recipe=None):
        super().__init__("GeoMorphX — DEM products", QgsTask.CanCancel)
        self.source, self.output_root, self.products = source, output_root, products
        self.recipe = normalize_recipe(recipe) if recipe is not None else create_recipe(products)
        self.receiver = weakref.ref(receiver)
        self.outputs, self.error = [], ""
        self.run_directory = None

    def run(self):
        try:
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:8]
            self.run_directory = Path(self.output_root) / ("geomorphx_" + stamp)
            execute_recipe(self.recipe, dem_path=self.source, out_dir=self.run_directory,
                           cancelled=self.isCanceled, progress=self.setProgress)
        except Exception as error:
            self.error = str(error)
        finally:
            if self.run_directory is not None:
                manifest = dict(format="geomorphx-run", schema_version="1.0", input_dem=self.source,
                                recipe=self.recipe, outputs=self.outputs,
                                status="failed" if self.error else "cancelled" if self.isCanceled() else "complete",
                                error=self.error)
                try:
                    source_manifest = self.run_directory / "recipe_run_manifest.json"
                    if source_manifest.exists():
                        manifest = json.loads(source_manifest.read_text(encoding="utf-8"))
                        self.outputs = [{"method": entry["method"], "path": entry["output"]}
                                        for entry in manifest["outputs"]]
                    self.run_directory.mkdir(parents=True, exist_ok=True)
                    (self.run_directory / "workflow.json").write_text(
                        json.dumps(manifest, indent=2, allow_nan=False), encoding="utf-8")
                except Exception as error:
                    self.error = self.error or str(error)
        return not self.error and not self.isCanceled()

    def finished(self, result):
        receiver = self.receiver()
        if receiver is not None and not sip.isdeleted(receiver):
            receiver.task_finished(self, result)


class GeoMorphXDock(QDockWidget):
    def __init__(self, iface):
        super().__init__("GeoMorphX — Terrain Workbench", iface.mainWindow())
        self.iface, self.task = iface, None
        self.recipe_context = {}
        self.setObjectName("GeoMorphXTerrainWorkbench")
        self.setMinimumWidth(360)
        self.setWindowIcon(QIcon(str(Path(__file__).with_name("icon.png"))))
        body = QWidget(self)
        layout = QVBoxLayout(body)
        header = QLabel("<h2>GeoMorphX</h2>Terrain products from your DEM")
        layout.addWidget(header)
        source = QGroupBox("1 · Input DEM")
        form = QFormLayout(source)
        self.layer_combo = QgsMapLayerComboBox()
        self.layer_combo.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.layer_combo.setAllowEmptyLayer(True)
        self.layer_combo.setLayer(iface.activeLayer() if isinstance(iface.activeLayer(), QgsRasterLayer) else None)
        form.addRow("Project layer", self.layer_combo)
        self.source_info = QLabel("Choose a single-band DEM with known elevation units.")
        self.source_info.setWordWrap(True)
        form.addRow(self.source_info)
        self.layer_combo.layerChanged.connect(self.update_source_info)
        layout.addWidget(source)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        products = QWidget()
        product_layout = QVBoxLayout(products)
        selector = QGroupBox("2 · Terrain products")
        select_layout = QVBoxLayout(selector)
        self.category = QComboBox()
        self.category.addItems(["Geomorphometry", "RRIM", "Terrain forms", "Hydrology (additional)", "All methods"])
        self.method = QComboBox()
        select_layout.addWidget(self.category)
        select_layout.addWidget(self.method)
        self.method_info = QLabel()
        self.method_info.setWordWrap(True)
        select_layout.addWidget(self.method_info)
        self.category.currentIndexChanged.connect(self.refresh_methods)
        self.method.currentIndexChanged.connect(self.update_parameters)
        product_layout.addWidget(selector)
        parameters = QGroupBox("3 · Parameters")
        parameter_form = QFormLayout(parameters)
        self.parameter_form = parameter_form
        self.window = QSpinBox(); self.window.setRange(3, 4095); self.window.setSingleStep(2); self.window.setValue(9)
        self.scales = QLineEdit("5,15,45")
        self.azimuth = QLineEdit("45")
        self.tile_size = QSpinBox(); self.tile_size.setRange(0, 8192); self.tile_size.setSingleStep(256); self.tile_size.setValue(512)
        self.flatness = QDoubleSpinBox(); self.flatness.setRange(0.000001, 89.999999); self.flatness.setDecimals(6); self.flatness.setValue(1)
        self.skip = QSpinBox(); self.skip.setRange(0, 2046)
        for label, widget in (("Window (pixels)", self.window), ("Scales (pixels)", self.scales),
                              ("Azimuth(s), degrees", self.azimuth), ("Block size; 0 = whole DEM", self.tile_size),
                              ("Geomorphon flatness (°)", self.flatness), ("Inner steps to skip", self.skip)):
            parameter_form.addRow(label, widget)
        self.weights = {}
        for name, value in (("directional_weight", .5), ("anisotropy_weight", .35),
                            ("roughness_weight", .25), ("structural_weight", .15)):
            spin = QDoubleSpinBox(); spin.setRange(0, 1); spin.setDecimals(3); spin.setSingleStep(.05); spin.setValue(value)
            self.weights[name] = spin
            parameter_form.addRow(name.replace("_", " ").capitalize(), spin)
        product_layout.addWidget(parameters)
        add = QPushButton("Add product")
        add.clicked.connect(self.add_product)
        product_layout.addWidget(add)
        note = QLabel("Every product uses the original DEM. This list is not a chain of filters.")
        note.setWordWrap(True)
        product_layout.addWidget(note)
        self.product_list = QListWidget()
        self.product_list.setMinimumHeight(100)
        self.product_list.setMaximumHeight(140)
        product_layout.addWidget(self.product_list)
        row = QHBoxLayout()
        for label, callback in (("Remove selected", self.remove_selected), ("Load recipe", self.load_recipe),
                                ("Save recipe", self.save_recipe)):
            button = QPushButton(label); button.clicked.connect(callback); row.addWidget(button)
        product_layout.addLayout(row)
        product_layout.addStretch()
        scroll.setWidget(products)
        self.tabs.addTab(scroll, "Products")
        self.log = QTextBrowser()
        self.tabs.addTab(self.log, "Run log")
        guide = QTextBrowser()
        guide.setHtml("<h3>DEM → terrain products → QGIS layers</h3><p>Add a projected, single-band DEM to the project. "
                      "Select methods and parameters, then run. Outputs and metadata go to a new run folder.</p>"
                      "<p>Horizontal and vertical units must match. Windows are in pixels. NoData is preserved.</p>"
                      "<p>RRIM variants are experimental compositions, not independently validated reproductions of classic RRIM. "
                      "Hydrology is an additional toolset and currently uses the whole DEM in memory.</p>"
                      "<p>Runs use a background QGIS task. Cancellation stops before the next product; "
                      "the current product finishes first. Completed outputs and logs are retained.</p>"
                      "<p>Processing tools also work with QGIS batch jobs and Model Designer. "
                      "Use the classic RRIM generator and RGB composer for the existing colour workflow.</p>")
        self.tabs.addTab(guide, "Guide")
        output = QGroupBox("4 · Outputs")
        output_layout = QVBoxLayout(output)
        directory_row = QHBoxLayout()
        self.output_dir = QLineEdit(QgsSettings().value("GeoMorphX/output_directory", QgsProject.instance().homePath(), type=str))
        browse = QPushButton("Browse…"); browse.clicked.connect(self.browse_output)
        directory_row.addWidget(self.output_dir); directory_row.addWidget(browse)
        output_layout.addLayout(directory_row)
        self.progress = QProgressBar()
        output_layout.addWidget(self.progress)
        actions = QHBoxLayout()
        self.run_button = QPushButton("Run and add layers")
        self.run_button.clicked.connect(self.run_products)
        self.cancel_button = QPushButton("Cancel after current product")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel_run)
        actions.addWidget(self.run_button); actions.addWidget(self.cancel_button)
        output_layout.addLayout(actions)
        layout.addWidget(output)
        self.setWidget(body)
        self.refresh_methods()
        self.update_source_info()

    def refresh_methods(self):
        self.method.clear()
        category = self.category.currentIndex()
        for method in METHODS:
            visible = (category == 4 or (category == 0 and method not in HYDROLOGY and
                       not method.startswith("rrim_") and not method.startswith("geomorphon")) or
                       (category == 1 and method.startswith("rrim_")) or
                       (category == 2 and method.startswith("geomorphon")) or
                       (category == 3 and method in HYDROLOGY))
            if visible:
                self.method.addItem(method_label(method), method)

    def update_parameters(self, *_args):
        if not hasattr(self, "weights"):
            return
        method = self.method.currentData() or ""
        if method in HYDROLOGY:
            self.method_info.setText("Additional hydrology tool: loads the full DEM. Block size does not bound RAM.")
        elif method.startswith("rrim_"):
            self.method_info.setText("Experimental RRIM composition. Global normalization uses retained scratch rasters.")
        elif method.startswith("geomorphon"):
            self.method_info.setText("Line-of-sight terrain forms. Window is a pixel diameter; NoData limits the search.")
        else:
            self.method_info.setText("Terrain derivative from the original DEM. Review resolution and elevation units.")
        widgets = {
            self.window: method.startswith("rrim_") or method.startswith("geomorphon") or
                         method in {"tpi", "tri", "local_relief", "wetness_proxy", "positive_openness", "negative_openness", "sky_view_factor"},
            self.scales: method.endswith("multiscale"),
            self.azimuth: "anisotropic" in method or "structural" in method or method == "rrim_plus",
            self.tile_size: method not in HYDROLOGY,
            self.flatness: method.startswith("geomorphon"),
            self.skip: method.startswith("geomorphon"),
            **{widget: ("anisotropic" in method if key == "directional_weight" else method == "rrim_plus")
               for key, widget in self.weights.items()},
        }
        for widget, visible in widgets.items():
            widget.setVisible(visible)
            label = self.parameter_form.labelForField(widget)
            if label is not None:
                label.setVisible(visible)

    def update_source_info(self, *_args):
        layer = self.layer_combo.currentLayer()
        if layer is None:
            self.source_info.setText("Choose a single-band DEM with known elevation units.")
        else:
            self.source_info.setText(f"{layer.width()} × {layer.height()} · {layer.crs().authid()} · "
                                     f"pixel {layer.rasterUnitsPerPixelX():g} × {layer.rasterUnitsPerPixelY():g}")

    def current_product(self):
        params = dict(window=self.window.value(), scales=[int(s.strip()) for s in self.scales.text().split(",") if s.strip()],
                      azimuth_deg=self.azimuth.text(), tile_size=self.tile_size.value(),
                      flatness_deg=self.flatness.value(), geomorphon_skip=self.skip.value(),
                      **{key: widget.value() for key, widget in self.weights.items()})
        product = dict(method=self.method.currentData(), parameters=params)
        validate_recipe(dict(format="geomorphx-workbench", version=1, products=[product]))
        return product

    def append_product(self, product):
        item = QListWidgetItem(f"{method_label(product['method'])} · window {product['parameters']['window']} px")
        item.setData(Qt.UserRole, product)
        item.setToolTip(json.dumps(product["parameters"], indent=2))
        self.product_list.addItem(item)

    def add_product(self):
        try:
            self.append_product(self.current_product())
        except Exception as error:
            QMessageBox.warning(self, "GeoMorphX parameters", str(error))

    def remove_selected(self):
        self.product_list.takeItem(self.product_list.currentRow())

    def products(self):
        return [self.product_list.item(i).data(Qt.UserRole) for i in range(self.product_list.count())]

    def save_recipe(self):
        try:
            data = self.recipe()
            path, _ = QFileDialog.getSaveFileName(self, "Save product recipe", "geomorphx_recipe.json", "JSON (*.json)")
            if path:
                save_recipe_file(data, path)
        except Exception as error:
            QMessageBox.warning(self, "GeoMorphX recipe", str(error))

    def load_recipe(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load product recipe", "", "JSON (*.json)")
        if not path:
            return
        try:
            self.set_recipe(load_recipe_file(path))
        except Exception as error:
            QMessageBox.warning(self, "GeoMorphX recipe", str(error))

    def browse_output(self):
        directory = QFileDialog.getExistingDirectory(self, "Output directory", self.output_dir.text())
        if directory:
            self.output_dir.setText(directory)

    def recipe(self):
        """Return the portable recipe, retaining imported resolution assumptions."""
        products = self.products() or [self.current_product()]
        return create_recipe(products, input_assumptions=self.recipe_context.get("input_assumptions"),
                             metadata=self.recipe_context.get("metadata"))

    def set_recipe(self, recipe):
        """Load canonical or legacy products without dialogs or processing."""
        normalized = normalize_recipe(recipe)
        self.product_list.clear()
        for product in normalized["products"]:
            self.append_product(product)
        self.recipe_context = {key: normalized[key] for key in ("input_assumptions", "metadata")}

    def run_products(self):
        try:
            if self.task is not None:
                return
            layer = self.layer_combo.currentLayer()
            if layer is None or not layer.isValid() or layer.bandCount() != 1:
                raise ValueError("Select a valid single-band DEM from the project.")
            if layer.crs().isGeographic() or not layer.crs().isValid():
                raise ValueError("Reproject the DEM to a suitable projected CRS first.")
            source = layer.source()
            if layer.providerType() != "gdal":
                raise ValueError("Export the selected layer to a local DEM GeoTIFF first.")
            recipe = self.recipe()
            products = recipe["products"]
            root = self.output_dir.text().strip()
            if not root:
                raise ValueError("Choose an output directory.")
            QgsSettings().setValue("GeoMorphX/output_directory", root)
            self.task = ProductTask(source, root, products, self, recipe=recipe)
            self.task.progressChanged.connect(lambda value: self.progress.setValue(int(value)))
            self.run_button.setEnabled(False); self.cancel_button.setEnabled(True)
            self.progress.setValue(0)
            self.log.append("Starting independent DEM products…")
            self.tabs.setCurrentIndex(1)
            QgsApplication.taskManager().addTask(self.task)
        except Exception as error:
            QMessageBox.warning(self, "GeoMorphX", str(error))

    def cancel_run(self):
        if self.task is not None:
            self.task.cancel()
            self.log.append("Cancellation requested; finishing the current product.")

    def task_finished(self, task, result):
        for output in task.outputs:
            layer = self.iface.addRasterLayer(output["path"], method_label(output["method"]))
            if layer and layer.isValid() and output["method"] == "geomorphons":
                labels = ["Flat", "Peak", "Ridge", "Shoulder", "Spur", "Slope", "Hollow", "Footslope", "Valley", "Pit"]
                colors = ["#cccccc", "#a50026", "#d73027", "#f46d43", "#fdae61", "#ffffbf", "#abd9e9", "#74add1", "#4575b4", "#313695"]
                classes = [QgsPalettedRasterRenderer.Class(i + 1, QColor(color), label)
                           for i, (label, color) in enumerate(zip(labels, colors))]
                layer.setRenderer(QgsPalettedRasterRenderer(layer.dataProvider(), 1, classes))
                layer.triggerRepaint()
            self.log.append("Added: " + output["path"])
        self.log.append(("Complete" if result else "Failed: " + task.error if task.error else "Cancelled") +
                        f" · {len(task.outputs)} products · {task.run_directory}")
        self.task = None
        self.run_button.setEnabled(True); self.cancel_button.setEnabled(False)
