# Standalone compatibility interface

QGIS is the primary GeoMorphX desktop interface. See the project README and
QGIS plugin guide for the workbench, ZIP installation and Processing tools.

The standalone GUI is retained for existing users and environments without
QGIS. It shares the 32-method core rather than maintaining separate numerical
implementations. Launch it with geomorphx-gui or run_standalone_gui.bat from a
configured environment. The separate geomorphx-standalone command provides
compute-batch and benchmark-batch.

The primary geomorphx CLI and Python API support portable recipe automation.
No new standalone installer has been produced. Method, memory and validation
limits are the same as in the shared core. See the development guide for Python
package setup; installing the QGIS ZIP does not install standalone command entry
points into another Python environment.
