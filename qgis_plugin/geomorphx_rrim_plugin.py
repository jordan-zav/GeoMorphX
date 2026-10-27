from qgis.core import QgsApplication
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from pathlib import Path
from .rrim_provider import RRIMProvider


class GeoMorphXRRIMPlugin:
    """QGIS-first lifecycle, including headless Processing registration."""

    def __init__(self, iface):
        self.iface = iface
        self.provider = None
        self.dock = None
        self.actions = []

    def initProcessing(self):
        if self.provider is None:
            self.provider = RRIMProvider()
            QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self):
        self.initProcessing()
        if self.iface is None or self.actions:
            return
        action = QAction(QIcon(str(Path(__file__).with_name("icon.png"))), "GeoMorphX Terrain Workbench", self.iface.mainWindow())
        action.triggered.connect(self.show_workbench)
        self.iface.addPluginToRasterMenu("GeoMorphX", action)
        self.iface.addToolBarIcon(action)
        self.actions.append(action)
        for label, name in (("Compute / batch / Model Designer…", "gmx_suite_compute"),
                            ("Compute DEM folder…", "gmx_suite_compute_batch"),
                            ("Classic RRIM generator…", "rrim_generator"),
                            ("Classic RRIM RGB composer…", "rrim_rgb_composer")):
            shortcut = QAction(label, self.iface.mainWindow())
            shortcut.triggered.connect(lambda checked=False, algorithm=name: self.open_algorithm(algorithm))
            self.iface.addPluginToRasterMenu("GeoMorphX", shortcut)
            self.actions.append(shortcut)

    def show_workbench(self):
        if self.dock is None:
            from .workbench import GeoMorphXDock
            self.dock = GeoMorphXDock(self.iface)
            self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dock)
        self.dock.show()
        self.dock.raise_()

    def open_algorithm(self, name):
        import processing
        processing.execAlgorithmDialog(self.provider.id() + ":" + name, {})

    def unload(self):
        if self.dock is not None:
            self.dock.cancel_run()
            if self.dock.task is not None:
                self.dock.task.progressChanged.disconnect()
            self.iface.removeDockWidget(self.dock)
            self.dock.deleteLater()
            self.dock = None
        for action in self.actions:
            self.iface.removePluginRasterMenu("GeoMorphX", action)
            self.iface.removeToolBarIcon(action)
            action.deleteLater()
        self.actions.clear()
        if self.provider:
            QgsApplication.processingRegistry().removeProvider(self.provider)
            self.provider = None
