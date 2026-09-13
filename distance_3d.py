# -*- coding: utf-8 -*-
"""Distance3D QGIS plugin main module.

Berechnet die 3D-Länge von Linien mit drei wählbaren Methoden:

1) Kartesisch (XY im DEM-CRS + Z aus DEM):
       sqrt(dx² + dy² + dz²)

2) Ellipsoid + ΔH:
       sqrt(d_ellipsoid² + dH²)

3) Geozentrisch / ECEF:
       sqrt(dX² + dY² + dZ²)

Bei Linien mit mehreren Stützpunkten wird jedes Segment einzeln berechnet
und anschließend zur Gesamtlänge addiert.

Azimut-Beschriftungen können unabhängig in Grad oder Gon gewählt werden.
Alle durch dieses Plugin gesetzten Beschriftungen verwenden #ffff00.
"""

import math
import os.path
from datetime import date

from qgis.PyQt.QtCore import QCoreApplication, QLocale, QTranslator, Qt, QVariant
from qgis.PyQt.QtGui import QColor, QIcon
from qgis.PyQt.QtWidgets import QAction, QButtonGroup

from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsDistanceArea,
    QgsField,
    QgsPalLayerSettings,
    QgsPointXY,
    QgsProject,
    QgsRasterLayer,
    QgsSettings,
    QgsTextFormat,
    QgsUnitTypes,
    QgsVectorLayer,
    QgsVectorLayerSimpleLabeling,
    QgsWkbTypes,
)

from .distance_3d_dockwidget import Distance3DDockWidget



class WMM2025:
    """Offline WMM2025 declination model (degree/order 12).

    Uses the official WMM2025 Gauss coefficients (epoch 2025.0).
    Declination is returned in degrees, east-positive.
    """

    EPOCH = 2025.0
    VALID_UNTIL = 2030.0
    MAXORD = 12
    A = 6378.137
    B = 6356.7523142
    RE = 6371.2

    COEFFICIENTS = ((1, 0, -29351.8, 0.0, 12.0, 0.0),
 (1, 1, -1410.8, 4545.4, 9.7, -21.5),
 (2, 0, -2556.6, 0.0, -11.6, 0.0),
 (2, 1, 2951.1, -3133.6, -5.2, -27.7),
 (2, 2, 1649.3, -815.1, -8.0, -12.1),
 (3, 0, 1361.0, 0.0, -1.3, 0.0),
 (3, 1, -2404.1, -56.6, -4.2, 4.0),
 (3, 2, 1243.8, 237.5, 0.4, -0.3),
 (3, 3, 453.6, -549.5, -15.6, -4.1),
 (4, 0, 895.0, 0.0, -1.6, 0.0),
 (4, 1, 799.5, 278.6, -2.4, -1.1),
 (4, 2, 55.7, -133.9, -6.0, 4.1),
 (4, 3, -281.1, 212.0, 5.6, 1.6),
 (4, 4, 12.1, -375.6, -7.0, -4.4),
 (5, 0, -233.2, 0.0, 0.6, 0.0),
 (5, 1, 368.9, 45.4, 1.4, -0.5),
 (5, 2, 187.2, 220.2, 0.0, 2.2),
 (5, 3, -138.7, -122.9, 0.6, 0.4),
 (5, 4, -142.0, 43.0, 2.2, 1.7),
 (5, 5, 20.9, 106.1, 0.9, 1.9),
 (6, 0, 64.4, 0.0, -0.2, 0.0),
 (6, 1, 63.8, -18.4, -0.4, 0.3),
 (6, 2, 76.9, 16.8, 0.9, -1.6),
 (6, 3, -115.7, 48.8, 1.2, -0.4),
 (6, 4, -40.9, -59.8, -0.9, 0.9),
 (6, 5, 14.9, 10.9, 0.3, 0.7),
 (6, 6, -60.7, 72.7, 0.9, 0.9),
 (7, 0, 79.5, 0.0, -0.0, 0.0),
 (7, 1, -77.0, -48.9, -0.1, 0.6),
 (7, 2, -8.8, -14.4, -0.1, 0.5),
 (7, 3, 59.3, -1.0, 0.5, -0.8),
 (7, 4, 15.8, 23.4, -0.1, 0.0),
 (7, 5, 2.5, -7.4, -0.8, -1.0),
 (7, 6, -11.1, -25.1, -0.8, 0.6),
 (7, 7, 14.2, -2.3, 0.8, -0.2),
 (8, 0, 23.2, 0.0, -0.1, 0.0),
 (8, 1, 10.8, 7.1, 0.2, -0.2),
 (8, 2, -17.5, -12.6, 0.0, 0.5),
 (8, 3, 2.0, 11.4, 0.5, -0.4),
 (8, 4, -21.7, -9.7, -0.1, 0.4),
 (8, 5, 16.9, 12.7, 0.3, -0.5),
 (8, 6, 15.0, 0.7, 0.2, -0.6),
 (8, 7, -16.8, -5.2, -0.0, 0.3),
 (8, 8, 0.9, 3.9, 0.2, 0.2),
 (9, 0, 4.6, 0.0, -0.0, 0.0),
 (9, 1, 7.8, -24.8, -0.1, -0.3),
 (9, 2, 3.0, 12.2, 0.1, 0.3),
 (9, 3, -0.2, 8.3, 0.3, -0.3),
 (9, 4, -2.5, -3.3, -0.3, 0.3),
 (9, 5, -13.1, -5.2, 0.0, 0.2),
 (9, 6, 2.4, 7.2, 0.3, -0.1),
 (9, 7, 8.6, -0.6, -0.1, -0.2),
 (9, 8, -8.7, 0.8, 0.1, 0.4),
 (9, 9, -12.9, 10.0, -0.1, 0.1),
 (10, 0, -1.3, 0.0, 0.1, 0.0),
 (10, 1, -6.4, 3.3, 0.0, 0.0),
 (10, 2, 0.2, 0.0, 0.1, -0.0),
 (10, 3, 2.0, 2.4, 0.1, -0.2),
 (10, 4, -1.0, 5.3, -0.0, 0.1),
 (10, 5, -0.6, -9.1, -0.3, -0.1),
 (10, 6, -0.9, 0.4, 0.0, 0.1),
 (10, 7, 1.5, -4.2, -0.1, 0.0),
 (10, 8, 0.9, -3.8, -0.1, -0.1),
 (10, 9, -2.7, 0.9, -0.0, 0.2),
 (10, 10, -3.9, -9.1, -0.0, -0.0),
 (11, 0, 2.9, 0.0, 0.0, 0.0),
 (11, 1, -1.5, 0.0, -0.0, -0.0),
 (11, 2, -2.5, 2.9, 0.0, 0.1),
 (11, 3, 2.4, -0.6, 0.0, -0.0),
 (11, 4, -0.6, 0.2, 0.0, 0.1),
 (11, 5, -0.1, 0.5, -0.1, -0.0),
 (11, 6, -0.6, -0.3, 0.0, -0.0),
 (11, 7, -0.1, -1.2, -0.0, 0.1),
 (11, 8, 1.1, -1.7, -0.1, -0.0),
 (11, 9, -1.0, -2.9, -0.1, 0.0),
 (11, 10, -0.2, -1.8, -0.1, 0.0),
 (11, 11, 2.6, -2.3, -0.1, 0.0),
 (12, 0, -2.0, 0.0, 0.0, 0.0),
 (12, 1, -0.2, -1.3, 0.0, -0.0),
 (12, 2, 0.3, 0.7, -0.0, 0.0),
 (12, 3, 1.2, 1.0, -0.0, -0.1),
 (12, 4, -1.3, -1.4, -0.0, 0.1),
 (12, 5, 0.6, -0.0, -0.0, -0.0),
 (12, 6, 0.6, 0.6, 0.1, -0.0),
 (12, 7, 0.5, -0.1, -0.0, -0.0),
 (12, 8, -0.1, 0.8, 0.0, 0.0),
 (12, 9, -0.4, 0.1, 0.0, -0.0),
 (12, 10, -0.2, -1.0, -0.1, -0.0),
 (12, 11, -1.3, 0.1, -0.0, 0.0),
 (12, 12, -0.7, 0.2, -0.1, -0.1))

    def __init__(self):
        size = self.MAXORD + 1
        self.a2 = self.A * self.A
        self.b2 = self.B * self.B
        self.c2 = self.a2 - self.b2
        self.a4 = self.a2 * self.a2
        self.b4 = self.b2 * self.b2
        self.c4 = self.a4 - self.b4

        self.c = [[0.0] * size for _ in range(size)]
        self.cd = [[0.0] * size for _ in range(size)]
        self.tc = [[0.0] * size for _ in range(size)]
        self.dp = [[0.0] * size for _ in range(size)]
        self.p = [[0.0] * size for _ in range(size)]
        self.sp = [0.0] * size
        self.cp = [0.0] * size
        self.fn = [0.0] * size
        self.fm = [0.0] * size
        self.pp = [0.0] * size
        self.k = [[0.0] * size for _ in range(size)]

        self.sp[0] = 0.0
        self.cp[0] = 1.0
        self.p[0][0] = 1.0
        self.pp[0] = 1.0
        self.dp[0][0] = 0.0

        for n, m, gnm, hnm, dgnm, dhnm in self.COEFFICIENTS:
            self.c[m][n] = gnm
            self.cd[m][n] = dgnm
            if m != 0:
                self.c[n][m - 1] = hnm
                self.cd[n][m - 1] = dhnm

        self.p[0][0] = 1.0
        self.fm[0] = 0.0

        for n in range(1, self.MAXORD + 1):
            self.p[0][n] = self.p[0][n - 1] * (2 * n - 1) / n
            j = 2
            for m in range(0, n + 1):
                self.k[m][n] = (
                    ((n - 1) * (n - 1) - m * m)
                    / ((2 * n - 1) * (2 * n - 3))
                )
                if m > 0:
                    flnmj = ((n - m + 1) * j) / (n + m)
                    self.p[m][n] = self.p[m - 1][n] * math.sqrt(flnmj)
                    j = 1
                    self.c[n][m - 1] *= self.p[m][n]
                    self.cd[n][m - 1] *= self.p[m][n]
                self.c[m][n] *= self.p[m][n]
                self.cd[m][n] *= self.p[m][n]
            self.fn[n] = n + 1
            self.fm[n] = n

        self.k[1][1] = 0.0

    def declination(self, latitude_deg, longitude_deg, altitude_m, decimal_year):
        """Return WMM2025 declination in degrees (east positive)."""
        if not (self.EPOCH <= decimal_year < self.VALID_UNTIL):
            raise ValueError("WMM2025 valid only for 2025.0 <= year < 2030.0")

        alt = float(altitude_m) / 1000.0
        dt = decimal_year - self.EPOCH
        dtr = math.pi / 180.0

        rlon = longitude_deg * dtr
        rlat = latitude_deg * dtr
        srlon = math.sin(rlon)
        crlon = math.cos(rlon)
        srlat = math.sin(rlat)
        crlat = math.cos(rlat)
        srlat2 = srlat * srlat
        crlat2 = crlat * crlat

        self.sp[0] = 0.0
        self.cp[0] = 1.0
        self.sp[1] = srlon
        self.cp[1] = crlon

        q = math.sqrt(self.a2 - self.c2 * srlat2)
        q1 = alt * q
        q2 = ((q1 + self.a2) / (q1 + self.b2)) ** 2
        ct = srlat / math.sqrt(q2 * crlat2 + srlat2)
        st = math.sqrt(max(0.0, 1.0 - ct * ct))
        r2 = alt * alt + 2.0 * q1 + (self.a4 - self.c4 * srlat2) / (q * q)
        r = math.sqrt(r2)
        d = math.sqrt(self.a2 * crlat2 + self.b2 * srlat2)
        ca = (alt + d) / r
        sa = self.c2 * crlat * srlat / (r * d)

        for m in range(2, self.MAXORD + 1):
            self.sp[m] = self.sp[1] * self.cp[m - 1] + self.cp[1] * self.sp[m - 1]
            self.cp[m] = self.cp[1] * self.cp[m - 1] - self.sp[1] * self.sp[m - 1]

        self.p[0][0] = 1.0
        self.dp[0][0] = 0.0
        self.pp = [0.0] * (self.MAXORD + 1)
        self.pp[0] = 1.0

        aor = self.RE / r
        ar = aor * aor
        br = bt = bp = bpp = 0.0

        for n in range(1, self.MAXORD + 1):
            ar *= aor
            for m in range(0, n + 1):
                if n == m:
                    self.p[m][n] = st * self.p[m - 1][n - 1]
                    self.dp[m][n] = st * self.dp[m - 1][n - 1] + ct * self.p[m - 1][n - 1]
                elif n == 1 and m == 0:
                    self.p[m][n] = ct * self.p[m][n - 1]
                    self.dp[m][n] = ct * self.dp[m][n - 1] - st * self.p[m][n - 1]
                elif n > 1 and n != m:
                    if m > n - 2:
                        self.p[m][n - 2] = 0.0
                        self.dp[m][n - 2] = 0.0
                    self.p[m][n] = ct * self.p[m][n - 1] - self.k[m][n] * self.p[m][n - 2]
                    self.dp[m][n] = (
                        ct * self.dp[m][n - 1]
                        - st * self.p[m][n - 1]
                        - self.k[m][n] * self.dp[m][n - 2]
                    )

                self.tc[m][n] = self.c[m][n] + dt * self.cd[m][n]
                if m != 0:
                    self.tc[n][m - 1] = self.c[n][m - 1] + dt * self.cd[n][m - 1]

                par = ar * self.p[m][n]
                if m == 0:
                    temp1 = self.tc[m][n] * self.cp[m]
                    temp2 = self.tc[m][n] * self.sp[m]
                else:
                    temp1 = self.tc[m][n] * self.cp[m] + self.tc[n][m - 1] * self.sp[m]
                    temp2 = self.tc[m][n] * self.sp[m] - self.tc[n][m - 1] * self.cp[m]

                bt -= ar * temp1 * self.dp[m][n]
                bp += self.fm[m] * temp2 * par
                br += self.fn[n] * temp1 * par

                if st == 0.0 and m == 1:
                    if n == 1:
                        self.pp[n] = self.pp[n - 1]
                    else:
                        self.pp[n] = ct * self.pp[n - 1] - self.k[m][n] * self.pp[n - 2]
                    bpp += self.fm[m] * temp2 * ar * self.pp[n]

        if st == 0.0:
            bp = bpp
        else:
            bp /= st

        bx = -bt * ca - br * sa
        by = bp
        return math.degrees(math.atan2(by, bx))


class Distance3D:
    """QGIS Plugin Implementation."""

    # Feldnamen sind absichtlich kurz (<= 10 Zeichen), damit sie auch mit
    # Formaten funktionieren, die kurze Feldnamen erzwingen (z. B. Shapefile).
    METHOD_INFO = {
        "cartesian": {
            "field": "L3D_Kart",
            "alias": "3D-Länge kartesisch [m]",
            "display": "Kartesisch",
        },
        "ellipsoid": {
            "field": "L3D_Elli",
            "alias": "3D-Länge ellipsoidisch [m]",
            "display": "Ellipsoidisch",
        },
        "geocentric": {
            "field": "L3D_ECEF",
            "alias": "3D-Länge geozentrisch / ECEF [m]",
            "display": "Geozentrisch / ECEF",
        },
    }

    AZIMUTH_INFO = {
        "degrees": {
            "az_field": "Azi_Grad",
            "dec_field": "Dekl_Grad",
            "az_alias": "Azimut geografisch [°]",
            "dec_alias": "Magnetische Deklination WMM2025 [°]",
            "factor": 1.0,
            "cycle": 360.0,
            "suffix": "°",
            "display": "Grad",
        },
        "gon": {
            "az_field": "Azi_Gon",
            "dec_field": "Dekl_Gon",
            "az_alias": "Azimut geografisch [gon]",
            "dec_alias": "Magnetische Deklination WMM2025 [gon]",
            "factor": 10.0 / 9.0,
            "cycle": 400.0,
            "suffix": " gon",
            "display": "Gon",
        },
    }

    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)

        locale = QgsSettings().value("locale/userLocale", QLocale().name())[0:2]
        locale_path = os.path.join(self.plugin_dir, "i18n", f"{locale}.qm")
        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        self.actions = []
        self.menu = self.tr("&Distance_3D")
        self.toolbar = self.iface.addToolBar("Distance3D")
        self.toolbar.setObjectName("Distance3D")

        self.pluginIsActive = False
        self.dockwidget = None
        self.calculation_button_group = None
        self.azimuth_unit_button_group = None
        self._project_signals_connected = False
        self.wmm2025 = WMM2025()

    # ------------------------------------------------------------------
    # QGIS Plugin-Grundfunktionen
    # ------------------------------------------------------------------

    def tr(self, message):
        return QCoreApplication.translate("Distance3D", message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None,
    ):
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)
        if whats_this is not None:
            action.setWhatsThis(whats_this)
        if add_to_toolbar:
            self.toolbar.addAction(action)
        if add_to_menu:
            self.iface.addPluginToMenu(self.menu, action)

        self.actions.append(action)
        return action

    def initGui(self):
        icon_path = os.path.join(self.plugin_dir, "icon.png")
        self.add_action(
            icon_path,
            text=self.tr("Beschriften des Layers - Layer labeling"),
            callback=self.run,
            parent=self.iface.mainWindow(),
        )

    def onClosePlugin(self):
        if self.dockwidget is not None:
            try:
                self.dockwidget.closingPlugin.disconnect(self.onClosePlugin)
            except (TypeError, RuntimeError):
                pass
        self.pluginIsActive = False

    def unload(self):
        self._disconnect_project_signals()

        for action in self.actions:
            self.iface.removePluginMenu(self.menu, action)
            self.iface.removeToolBarIcon(action)

        if self.dockwidget is not None:
            self.iface.removeDockWidget(self.dockwidget)

        if hasattr(self, "toolbar") and self.toolbar is not None:
            del self.toolbar

    # ------------------------------------------------------------------
    # Dock Widget / UI
    # ------------------------------------------------------------------

    def run(self):
        if not self.pluginIsActive:
            self.pluginIsActive = True

            if self.dockwidget is None:
                self.dockwidget = Distance3DDockWidget()

                if not self._validate_ui():
                    self.pluginIsActive = False
                    return

                # Buttons nur EINMAL verbinden.
                self.dockwidget.pushButton_close.clicked.connect(
                    self.dockwidget.close
                )
                self.dockwidget.pushButton_ok.clicked.connect(
                    lambda checked=False: self.calculate_3d_distance()
                )
                self.dockwidget.pushButton_refresh.clicked.connect(
                    lambda checked=False: self.refresh_window()
                )
                self.dockwidget.pushButton_degrees.clicked.connect(
                    lambda checked=False: self.calculate_azimuth_fields("degrees")
                )
                self.dockwidget.pushButton_gon.clicked.connect(
                    lambda checked=False: self.calculate_azimuth_fields("gon")
                )
                self.dockwidget.pushButton_geographic.clicked.connect(
                    lambda checked=False: self.apply_azimuth_label(False)
                )
                self.dockwidget.pushButton_magnetic.clicked.connect(
                    lambda checked=False: self.apply_azimuth_label(True)
                )
                self.dockwidget.pushButton_reset.clicked.connect(
                    lambda checked=False: self.reset_labels()
                )

                # Exklusive Auswahl der Berechnungsmethode.
                self.calculation_button_group = QButtonGroup(self.dockwidget)
                self.calculation_button_group.setExclusive(True)
                self.calculation_button_group.addButton(
                    self.dockwidget.radioButton_karthesic
                )
                self.calculation_button_group.addButton(
                    self.dockwidget.radioButton_ellipsoid
                )
                self.calculation_button_group.addButton(
                    self.dockwidget.radioButton_geocentric
                )

                if not any(
                    (
                        self.dockwidget.radioButton_karthesic.isChecked(),
                        self.dockwidget.radioButton_ellipsoid.isChecked(),
                        self.dockwidget.radioButton_geocentric.isChecked(),
                    )
                ):
                    self.dockwidget.radioButton_karthesic.setChecked(True)

                # Exklusive, von der Längenmethode unabhängige Auswahl der
                # Einheit für die Azimut-BESCHRIFTUNG. Dadurch können z. B.
                # Grad- und Gon-Spalten gleichzeitig existieren, während der
                # Benutzer eindeutig festlegt, welche Einheit ins Label kommt.
                self.azimuth_unit_button_group = QButtonGroup(self.dockwidget)
                self.azimuth_unit_button_group.setExclusive(True)
                self.azimuth_unit_button_group.addButton(
                    self.dockwidget.radioButton_degrees
                )
                self.azimuth_unit_button_group.addButton(
                    self.dockwidget.radioButton_gon
                )

                if not (
                    self.dockwidget.radioButton_degrees.isChecked()
                    or self.dockwidget.radioButton_gon.isChecked()
                ):
                    self.dockwidget.radioButton_degrees.setChecked(True)

                self._connect_project_signals()

            try:
                self.dockwidget.closingPlugin.connect(self.onClosePlugin)
            except (TypeError, RuntimeError):
                pass

            self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dockwidget)

        # Beim Öffnen immer neu einlesen.
        self.refresh_window(show_message=False)
        self.dockwidget.show()
        self.dockwidget.raise_()

    def _validate_ui(self):
        required = (
            "comboBox_dem",
            "comboBox_vector",
            "pushButton_close",
            "pushButton_ok",
            "pushButton_refresh",
            "pushButton_degrees",
            "pushButton_gon",
            "pushButton_geographic",
            "pushButton_magnetic",
            "pushButton_reset",
            "radioButton_karthesic",
            "radioButton_ellipsoid",
            "radioButton_geocentric",
            "radioButton_degrees",
            "radioButton_gon",
        )
        missing = [name for name in required if not hasattr(self.dockwidget, name)]
        if missing:
            self.iface.messageBar().pushCritical(
                "Distance 3D",
                "Folgende UI-Objekte fehlen oder haben einen anderen objectName: "
                + ", ".join(missing),
            )
            return False
        return True

    def _connect_project_signals(self):
        """Layerlisten auch bei Änderungen am Projekt automatisch aktualisieren."""
        if self._project_signals_connected:
            return

        project = QgsProject.instance()
        project.layersAdded.connect(self._on_project_layers_changed)
        project.layersRemoved.connect(self._on_project_layers_changed)
        self._project_signals_connected = True

    def _disconnect_project_signals(self):
        if not self._project_signals_connected:
            return

        project = QgsProject.instance()
        try:
            project.layersAdded.disconnect(self._on_project_layers_changed)
        except (TypeError, RuntimeError):
            pass
        try:
            project.layersRemoved.disconnect(self._on_project_layers_changed)
        except (TypeError, RuntimeError):
            pass
        self._project_signals_connected = False

    def _on_project_layers_changed(self, *args):
        if self.dockwidget is not None:
            self.refresh_window(show_message=False)

    def refresh_window(self, show_message=True):
        """ComboBoxen aus dem AKTUELLEN Projekt neu aufbauen."""
        if self.dockwidget is None:
            return

        old_dem_id = self.dockwidget.comboBox_dem.currentData()
        old_vector_id = self.dockwidget.comboBox_vector.currentData()

        self.dockwidget.comboBox_dem.blockSignals(True)
        self.dockwidget.comboBox_vector.blockSignals(True)

        try:
            self.dockwidget.comboBox_dem.clear()
            self.dockwidget.comboBox_vector.clear()

            # mapLayers() direkt bei jedem Refresh erneut abfragen.
            layers = list(QgsProject.instance().mapLayers().values())

            raster_layers = [
                layer for layer in layers if isinstance(layer, QgsRasterLayer)
            ]
            line_layers = [
                layer
                for layer in layers
                if isinstance(layer, QgsVectorLayer)
                and layer.geometryType() == QgsWkbTypes.LineGeometry
            ]

            raster_layers.sort(key=lambda layer: layer.name().lower())
            line_layers.sort(key=lambda layer: layer.name().lower())

            for layer in raster_layers:
                self.dockwidget.comboBox_dem.addItem(layer.name(), layer.id())

            for layer in line_layers:
                self.dockwidget.comboBox_vector.addItem(layer.name(), layer.id())

            self._restore_combobox_selection(
                self.dockwidget.comboBox_dem, old_dem_id
            )
            self._restore_combobox_selection(
                self.dockwidget.comboBox_vector, old_vector_id
            )

        finally:
            self.dockwidget.comboBox_dem.blockSignals(False)
            self.dockwidget.comboBox_vector.blockSignals(False)

        self.dockwidget.update()
        self.dockwidget.repaint()

        if show_message:
            self.iface.messageBar().pushSuccess(
                "Distance 3D",
                "Layerlisten wurden aktualisiert.",
            )

    @staticmethod
    def _restore_combobox_selection(combo_box, layer_id):
        if layer_id is None:
            if combo_box.count() > 0:
                combo_box.setCurrentIndex(0)
            return

        for index in range(combo_box.count()):
            if combo_box.itemData(index) == layer_id:
                combo_box.setCurrentIndex(index)
                return

        if combo_box.count() > 0:
            combo_box.setCurrentIndex(0)

    # ------------------------------------------------------------------
    # Hauptberechnung
    # ------------------------------------------------------------------

    def calculate_3d_distance(self):
        raster_id = self.dockwidget.comboBox_dem.currentData()
        vector_id = self.dockwidget.comboBox_vector.currentData()

        if raster_id is None or vector_id is None:
            self.iface.messageBar().pushWarning(
                "Distance 3D",
                "Bitte einen DEM- und einen Linienlayer auswählen.",
            )
            return

        raster_layer = QgsProject.instance().mapLayer(raster_id)
        vector_layer = QgsProject.instance().mapLayer(vector_id)

        if raster_layer is None or vector_layer is None:
            self.iface.messageBar().pushCritical(
                "Distance 3D",
                "Ein ausgewählter Layer wurde nicht gefunden.",
            )
            return

        if raster_layer.bandCount() < 1:
            self.iface.messageBar().pushCritical(
                "Distance 3D",
                "Der ausgewählte Rasterlayer besitzt kein Rasterband.",
            )
            return

        method = self._selected_method()
        if method is None:
            self.iface.messageBar().pushWarning(
                "Distance 3D",
                "Bitte eine Berechnungsmethode auswählen.",
            )
            return

        method_info = self.METHOD_INFO[method]
        field_name = method_info["field"]

        # Transformation für die DEM-Abfrage.
        vector_to_dem = QgsCoordinateTransform(
            vector_layer.crs(),
            raster_layer.crs(),
            QgsProject.instance(),
        )

        # --------------------------------------------------------------
        # Kartesisch:
        # XY werden im DEM-CRS berechnet, NICHT im Vektor-CRS.
        # So entsteht nicht der typische Fehler, bei dem Gradwerte mit
        # Höhenmetern kombiniert werden und z. B. ~10 m statt ~2000 m
        # herauskommen.
        # --------------------------------------------------------------
        cartesian_unit_factor = None
        if method == "cartesian":
            if raster_layer.crs().isGeographic():
                self.iface.messageBar().pushCritical(
                    "Distance 3D",
                    "Kartesisch kann nur mit einem DEM in einem projizierten "
                    "CRS berechnet werden. Das DEM-CRS ist geografisch (Grad). "
                    "Bitte ein projiziertes DEM verwenden oder Ellipsoid/ECEF "
                    "auswählen.",
                )
                return

            try:
                cartesian_unit_factor = QgsUnitTypes.fromUnitToUnitFactor(
                    raster_layer.crs().mapUnits(),
                    QgsUnitTypes.DistanceMeters,
                )
            except Exception:
                cartesian_unit_factor = 1.0

            if not math.isfinite(cartesian_unit_factor) or cartesian_unit_factor <= 0:
                cartesian_unit_factor = 1.0

        # --------------------------------------------------------------
        # Ellipsoidische horizontale Entfernung.
        # --------------------------------------------------------------
        distance_area = None
        if method == "ellipsoid":
            distance_area = QgsDistanceArea()
            distance_area.setSourceCrs(
                vector_layer.crs(),
                QgsProject.instance().transformContext(),
            )

            ellipsoid = QgsProject.instance().ellipsoid()
            if not ellipsoid or str(ellipsoid).upper() == "NONE":
                ellipsoid = "WGS84"
            distance_area.setEllipsoid(ellipsoid)

        # --------------------------------------------------------------
        # Geozentrisch / ECEF benötigt Längengrad/Breitengrad.
        # --------------------------------------------------------------
        vector_to_wgs84 = None
        if method == "geocentric":
            wgs84 = QgsCoordinateReferenceSystem("EPSG:4326")
            vector_to_wgs84 = QgsCoordinateTransform(
                vector_layer.crs(),
                wgs84,
                QgsProject.instance(),
            )

        # --------------------------------------------------------------
        # Methodenabhängiges Ergebnisfeld erstellen / verwenden.
        # --------------------------------------------------------------
        was_editing = vector_layer.isEditable()
        if not was_editing and not vector_layer.startEditing():
            self.iface.messageBar().pushCritical(
                "Distance 3D",
                "Der Vektorlayer kann nicht bearbeitet werden.",
            )
            return

        field_index = self._ensure_result_field(
            vector_layer,
            field_name,
            method_info["alias"],
        )

        if field_index < 0:
            if not was_editing:
                vector_layer.rollBack()
            return

        provider = raster_layer.dataProvider()
        calculated = 0
        failed = 0

        for feature in vector_layer.getFeatures():
            geometry = feature.geometry()

            if geometry is None or geometry.isEmpty():
                vector_layer.changeAttributeValue(feature.id(), field_index, None)
                failed += 1
                continue

            lines = self._geometry_to_lines(geometry)
            if not lines:
                vector_layer.changeAttributeValue(feature.id(), field_index, None)
                failed += 1
                continue

            total_length_3d = 0.0
            feature_valid = True
            has_segment = False

            for line in lines:
                if len(line) < 2:
                    continue

                has_segment = True
                previous_point = line[0]
                previous_dem_point, previous_z = self._sample_dem_point_and_height(
                    previous_point,
                    provider,
                    vector_to_dem,
                )

                if previous_z is None:
                    feature_valid = False
                    break

                for point in line[1:]:
                    dem_point, z = self._sample_dem_point_and_height(
                        point,
                        provider,
                        vector_to_dem,
                    )

                    if z is None:
                        feature_valid = False
                        break

                    if method == "cartesian":
                        segment_length = self._segment_cartesian(
                            previous_dem_point,
                            dem_point,
                            previous_z,
                            z,
                            cartesian_unit_factor,
                        )

                    elif method == "ellipsoid":
                        segment_length = self._segment_ellipsoid(
                            previous_point,
                            point,
                            previous_z,
                            z,
                            distance_area,
                        )

                    else:
                        segment_length = self._segment_geocentric(
                            previous_point,
                            point,
                            previous_z,
                            z,
                            vector_to_wgs84,
                        )

                    if segment_length is None or not math.isfinite(segment_length):
                        feature_valid = False
                        break

                    total_length_3d += segment_length

                    previous_point = point
                    previous_dem_point = dem_point
                    previous_z = z

                if not feature_valid:
                    break

            if feature_valid and has_segment:
                vector_layer.changeAttributeValue(
                    feature.id(),
                    field_index,
                    round(total_length_3d, 2),
                )
                calculated += 1
            else:
                vector_layer.changeAttributeValue(feature.id(), field_index, None)
                failed += 1

        if not was_editing:
            if not vector_layer.commitChanges():
                errors = vector_layer.commitErrors()
                vector_layer.rollBack()
                error_text = "; ".join(errors) if errors else "Unbekannter Fehler"
                self.iface.messageBar().pushCritical(
                    "Distance 3D",
                    "Die berechneten Werte konnten nicht gespeichert werden: "
                    + error_text,
                )
                return

            # Nach Commit Index ggf. neu bestimmen.
            field_index = vector_layer.fields().indexFromName(field_name)

        # Beschriftung IMMER auf das Feld der aktuell berechneten Methode setzen.
        self.enable_3d_labels(vector_layer, field_name)
        vector_layer.triggerRepaint()

        message = (
            f"{calculated} Linie(n) mit '{method_info['display']}' berechnet. "
            f"Ergebnisfeld: {field_name}."
        )
        if failed > 0:
            message += (
                f" {failed} Linie(n) konnten wegen fehlender DEM-Werte "
                "oder ungültiger Geometrie nicht berechnet werden."
            )

        self.iface.messageBar().pushSuccess("Distance 3D", message)

    def _ensure_result_field(self, vector_layer, field_name, alias, precision=2):
        """Numerisches Ergebnisfeld erzeugen, falls es noch fehlt."""
        field_index = vector_layer.fields().indexFromName(field_name)

        if field_index == -1:
            success = vector_layer.addAttribute(
                QgsField(field_name, QVariant.Double, len=20, prec=precision)
            )
            if not success:
                self.iface.messageBar().pushCritical(
                    "Distance 3D",
                    f"Das Ergebnisfeld '{field_name}' konnte nicht angelegt werden.",
                )
                return -1

            vector_layer.updateFields()
            field_index = vector_layer.fields().indexFromName(field_name)

        # Lesbarer Alias in der Attributtabelle.
        if field_index >= 0:
            try:
                vector_layer.setFieldAlias(field_index, alias)
            except Exception:
                pass

        return field_index


    # ------------------------------------------------------------------
    # Azimut / WMM2025
    # ------------------------------------------------------------------

    def calculate_azimuth_fields(self, unit="degrees", show_message=True):
        """Berechnet geografischen Azimut und WMM2025-Deklination."""
        if unit not in self.AZIMUTH_INFO:
            return False

        vector_id = self.dockwidget.comboBox_vector.currentData()
        if vector_id is None:
            self.iface.messageBar().pushWarning(
                "Distance 3D", "Bitte einen Linienlayer auswählen."
            )
            return False

        vector_layer = QgsProject.instance().mapLayer(vector_id)
        if not isinstance(vector_layer, QgsVectorLayer):
            self.iface.messageBar().pushCritical(
                "Distance 3D", "Der ausgewählte Vektorlayer wurde nicht gefunden."
            )
            return False

        decimal_year = self._current_decimal_year()
        if not (WMM2025.EPOCH <= decimal_year < WMM2025.VALID_UNTIL):
            self.iface.messageBar().pushCritical(
                "Distance 3D",
                "WMM2025 ist nur für 2025.0 bis vor 2030.0 gültig.",
            )
            return False

        info = self.AZIMUTH_INFO[unit]
        distance_area = QgsDistanceArea()
        distance_area.setSourceCrs(
            vector_layer.crs(),
            QgsProject.instance().transformContext(),
        )
        distance_area.setEllipsoid("WGS84")

        wgs84 = QgsCoordinateReferenceSystem("EPSG:4326")
        vector_to_wgs84 = QgsCoordinateTransform(
            vector_layer.crs(), wgs84, QgsProject.instance()
        )

        raster_layer = None
        wgs84_to_dem = None
        raster_id = self.dockwidget.comboBox_dem.currentData()
        if raster_id is not None:
            candidate = QgsProject.instance().mapLayer(raster_id)
            if isinstance(candidate, QgsRasterLayer) and candidate.bandCount() >= 1:
                raster_layer = candidate
                wgs84_to_dem = QgsCoordinateTransform(
                    wgs84, raster_layer.crs(), QgsProject.instance()
                )

        was_editing = vector_layer.isEditable()
        if not was_editing and not vector_layer.startEditing():
            self.iface.messageBar().pushCritical(
                "Distance 3D", "Der Vektorlayer kann nicht bearbeitet werden."
            )
            return False

        az_index = self._ensure_result_field(
            vector_layer, info["az_field"], info["az_alias"], precision=4
        )
        dec_index = self._ensure_result_field(
            vector_layer, info["dec_field"], info["dec_alias"], precision=4
        )

        if az_index < 0 or dec_index < 0:
            if not was_editing:
                vector_layer.rollBack()
            return False

        calculated = 0
        failed = 0

        for feature in vector_layer.getFeatures():
            endpoints = self._line_endpoints(feature.geometry())

            if endpoints is None:
                vector_layer.changeAttributeValue(feature.id(), az_index, None)
                vector_layer.changeAttributeValue(feature.id(), dec_index, None)
                failed += 1
                continue

            start_point, end_point = endpoints

            try:
                bearing_rad = distance_area.bearing(
                    QgsPointXY(start_point), QgsPointXY(end_point)
                )
                azimuth_deg = math.degrees(bearing_rad) % 360.0

                start_ll = vector_to_wgs84.transform(QgsPointXY(start_point))
                end_ll = vector_to_wgs84.transform(QgsPointXY(end_point))
                mid_lat, mid_lon = self._great_circle_midpoint(
                    start_ll.y(), start_ll.x(), end_ll.y(), end_ll.x()
                )

                altitude_m = 0.0
                if raster_layer is not None and wgs84_to_dem is not None:
                    try:
                        dem_point = wgs84_to_dem.transform(QgsPointXY(mid_lon, mid_lat))
                        value, ok = raster_layer.dataProvider().sample(dem_point, 1)
                        if self._is_valid_dem_value(value, ok):
                            altitude_m = float(value)
                    except Exception:
                        altitude_m = 0.0

                declination_deg = self.wmm2025.declination(
                    mid_lat, mid_lon, altitude_m, decimal_year
                )

                azimuth_value = (azimuth_deg * info["factor"]) % info["cycle"]
                declination_value = declination_deg * info["factor"]

                vector_layer.changeAttributeValue(
                    feature.id(), az_index, round(azimuth_value, 4)
                )
                vector_layer.changeAttributeValue(
                    feature.id(), dec_index, round(declination_value, 4)
                )
                calculated += 1

            except Exception:
                vector_layer.changeAttributeValue(feature.id(), az_index, None)
                vector_layer.changeAttributeValue(feature.id(), dec_index, None)
                failed += 1

        if not was_editing:
            if not vector_layer.commitChanges():
                errors = vector_layer.commitErrors()
                vector_layer.rollBack()
                error_text = "; ".join(errors) if errors else "Unbekannter Fehler"
                self.iface.messageBar().pushCritical(
                    "Distance 3D",
                    "Azimut/Deklination konnten nicht gespeichert werden: " + error_text,
                )
                return False

        vector_layer.triggerRepaint()

        if show_message:
            message = (
                f"{calculated} Linie(n): Azimut und WMM2025-Deklination "
                f"in {info['display']} berechnet."
            )
            if failed:
                message += f" {failed} Linie(n) konnten nicht berechnet werden."
            self.iface.messageBar().pushSuccess("Distance 3D", message)

        return True

    def apply_azimuth_label(self, magnetic=False):
        """Beschriftung = aktuelle 3D-Länge + geografischer/magnetischer Azimut."""
        vector_id = self.dockwidget.comboBox_vector.currentData()
        if vector_id is None:
            self.iface.messageBar().pushWarning(
                "Distance 3D", "Bitte einen Linienlayer auswählen."
            )
            return

        vector_layer = QgsProject.instance().mapLayer(vector_id)
        if not isinstance(vector_layer, QgsVectorLayer):
            return

        method = self._selected_method()
        if method is None:
            self.iface.messageBar().pushWarning(
                "Distance 3D",
                "Bitte eine Berechnungsmethode für die 3D-Länge auswählen.",
            )
            return

        length_field = self.METHOD_INFO[method]["field"]
        if vector_layer.fields().indexFromName(length_field) < 0:
            self.iface.messageBar().pushWarning(
                "Distance 3D",
                "Für die gewählte Längenmethode existiert noch kein Ergebnisfeld. "
                "Bitte zuerst mit OK die 3D-Länge berechnen.",
            )
            return

        unit = self._selected_azimuth_unit()
        if unit is None:
            self.iface.messageBar().pushWarning(
                "Distance 3D",
                "Bitte für die Azimut-Beschriftung Grad oder Gon auswählen.",
            )
            return

        info = self.AZIMUTH_INFO[unit]

        if (
            vector_layer.fields().indexFromName(info["az_field"]) < 0
            or vector_layer.fields().indexFromName(info["dec_field"]) < 0
        ):
            if not self.calculate_azimuth_fields(unit, show_message=False):
                return

        az_field = info["az_field"]
        dec_field = info["dec_field"]
        suffix = info["suffix"].replace("'", "''")

        if magnetic:
            cycle = int(info["cycle"])
            az_expression = (
                f'(("{az_field}" - "{dec_field}" + {cycle}) % {cycle})'
            )
            label_name = "Azi mag"
        else:
            az_expression = f'"{az_field}"'
            label_name = "Azi geo"

        expression = (
            f'format_number("{length_field}", 2) || \' m | {label_name}: \' || '
            f'format_number({az_expression}, 2) || \'{suffix}\''
        )
        self._set_label_expression(vector_layer, expression)

    def reset_labels(self):
        """Beschriftung ausschalten, ohne Felder/Spalten zu löschen."""
        vector_id = self.dockwidget.comboBox_vector.currentData()
        if vector_id is None:
            return

        vector_layer = QgsProject.instance().mapLayer(vector_id)
        if not isinstance(vector_layer, QgsVectorLayer):
            return

        vector_layer.setLabelsEnabled(False)
        vector_layer.triggerRepaint()
        self.iface.messageBar().pushSuccess(
            "Distance 3D",
            "Beschriftung zurückgesetzt; Attributspalten bleiben erhalten.",
        )

    def _set_label_expression(self, vector_layer, expression):
        """Zentrale Label-Funktion; alle Plugin-Labels sind #ffff00."""
        settings = QgsPalLayerSettings()
        settings.fieldName = expression
        settings.isExpression = True
        settings.placement = QgsPalLayerSettings.Line

        text_format = QgsTextFormat()
        text_format.setColor(QColor("#ffff00"))
        settings.setFormat(text_format)

        vector_layer.setLabeling(QgsVectorLayerSimpleLabeling(settings))
        vector_layer.setLabelsEnabled(True)
        vector_layer.triggerRepaint()

    @staticmethod
    def _line_endpoints(geometry):
        """Erster und letzter Stützpunkt einer Single-/Multipart-Linie."""
        if geometry is None or geometry.isEmpty():
            return None

        lines = Distance3D._geometry_to_lines(geometry)
        valid_lines = [line for line in lines if len(line) >= 2]
        if not valid_lines:
            return None

        start_point = valid_lines[0][0]
        end_point = valid_lines[-1][-1]
        if (
            math.isclose(start_point.x(), end_point.x(), rel_tol=0.0, abs_tol=1e-15)
            and math.isclose(start_point.y(), end_point.y(), rel_tol=0.0, abs_tol=1e-15)
        ):
            return None

        return start_point, end_point

    @staticmethod
    def _great_circle_midpoint(lat1_deg, lon1_deg, lat2_deg, lon2_deg):
        """Sphärischer Mittelpunkt zweier WGS84-Positionen."""
        lat1 = math.radians(lat1_deg)
        lon1 = math.radians(lon1_deg)
        lat2 = math.radians(lat2_deg)
        lon2 = math.radians(lon2_deg)

        x = math.cos(lat1) * math.cos(lon1) + math.cos(lat2) * math.cos(lon2)
        y = math.cos(lat1) * math.sin(lon1) + math.cos(lat2) * math.sin(lon2)
        z = math.sin(lat1) + math.sin(lat2)

        if abs(x) + abs(y) + abs(z) < 1e-15:
            return (lat1_deg + lat2_deg) / 2.0, (lon1_deg + lon2_deg) / 2.0

        lon = math.atan2(y, x)
        hyp = math.sqrt(x * x + y * y)
        lat = math.atan2(z, hyp)
        return math.degrees(lat), math.degrees(lon)

    @staticmethod
    def _current_decimal_year():
        today = date.today()
        start = date(today.year, 1, 1)
        end = date(today.year + 1, 1, 1)
        return today.year + (today - start).days / (end - start).days

    # ------------------------------------------------------------------
    # Methodenwahl
    # ------------------------------------------------------------------

    def _selected_method(self):
        if self.dockwidget.radioButton_karthesic.isChecked():
            return "cartesian"
        if self.dockwidget.radioButton_ellipsoid.isChecked():
            return "ellipsoid"
        if self.dockwidget.radioButton_geocentric.isChecked():
            return "geocentric"
        return None

    def _selected_azimuth_unit(self):
        """Einheit, die für geografische/magnetische Labels verwendet wird."""
        if self.dockwidget.radioButton_degrees.isChecked():
            return "degrees"
        if self.dockwidget.radioButton_gon.isChecked():
            return "gon"
        return None

    # ------------------------------------------------------------------
    # 1) Kartesisch
    # ------------------------------------------------------------------

    @staticmethod
    def _segment_cartesian(dem_point1, dem_point2, z1, z2, unit_factor):
        """Kartesische 3D-Länge in Metern, XY aus dem DEM-CRS."""
        dx = (dem_point2.x() - dem_point1.x()) * unit_factor
        dy = (dem_point2.y() - dem_point1.y()) * unit_factor
        dz = z2 - z1
        return math.sqrt(dx * dx + dy * dy + dz * dz)

    # ------------------------------------------------------------------
    # 2) Ellipsoid + ΔH
    # ------------------------------------------------------------------

    @staticmethod
    def _segment_ellipsoid(point1, point2, z1, z2, distance_area):
        """sqrt(ellipsoidische horizontale Distanz² + Höhendifferenz²)."""
        horizontal_distance = distance_area.measureLine(
            QgsPointXY(point1),
            QgsPointXY(point2),
        )

        # Explizit in Meter umrechnen, unabhängig davon, welche Einheit
        # QgsDistanceArea intern für das Ergebnis meldet.
        try:
            horizontal_distance = distance_area.convertLengthMeasurement(
                horizontal_distance,
                QgsUnitTypes.DistanceMeters,
            )
        except Exception:
            # Mit gesetztem Ellipsoid liefert QGIS üblicherweise ohnehin Meter.
            pass

        dz = z2 - z1
        return math.sqrt(
            horizontal_distance * horizontal_distance + dz * dz
        )

    # ------------------------------------------------------------------
    # 3) Geozentrisch / ECEF
    # ------------------------------------------------------------------

    def _segment_geocentric(self, point1, point2, z1, z2, vector_to_wgs84):
        lon_lat_1 = vector_to_wgs84.transform(QgsPointXY(point1))
        lon_lat_2 = vector_to_wgs84.transform(QgsPointXY(point2))

        x1, y1, z_ecef_1 = self._wgs84_to_ecef(
            lon_lat_1.x(),
            lon_lat_1.y(),
            z1,
        )
        x2, y2, z_ecef_2 = self._wgs84_to_ecef(
            lon_lat_2.x(),
            lon_lat_2.y(),
            z2,
        )

        dx = x2 - x1
        dy = y2 - y1
        dz = z_ecef_2 - z_ecef_1
        return math.sqrt(dx * dx + dy * dy + dz * dz)

    @staticmethod
    def _wgs84_to_ecef(longitude_deg, latitude_deg, height):
        """WGS84 geografisch -> ECEF (X/Y/Z in Metern)."""
        a = 6378137.0
        f = 1.0 / 298.257223563
        e2 = f * (2.0 - f)

        lon = math.radians(longitude_deg)
        lat = math.radians(latitude_deg)

        sin_lat = math.sin(lat)
        cos_lat = math.cos(lat)
        sin_lon = math.sin(lon)
        cos_lon = math.cos(lon)

        n = a / math.sqrt(1.0 - e2 * sin_lat * sin_lat)

        x = (n + height) * cos_lat * cos_lon
        y = (n + height) * cos_lat * sin_lon
        z = (n * (1.0 - e2) + height) * sin_lat
        return x, y, z

    # ------------------------------------------------------------------
    # DEM / Geometrie-Hilfsfunktionen
    # ------------------------------------------------------------------

    def _sample_dem_point_and_height(self, point, provider, vector_to_dem):
        """Punkt ins DEM-CRS transformieren und Höhe aus Band 1 abfragen."""
        try:
            dem_point = vector_to_dem.transform(QgsPointXY(point))
            value, ok = provider.sample(dem_point, 1)
        except Exception:
            return None, None

        if not self._is_valid_dem_value(value, ok):
            return dem_point, None

        return dem_point, float(value)

    @staticmethod
    def _is_valid_dem_value(value, ok):
        if not ok or value is None:
            return False
        try:
            return math.isfinite(float(value))
        except (TypeError, ValueError):
            return False

    @staticmethod
    def _geometry_to_lines(geometry):
        """Single-/Multipart-Linien liefern; Kurven bei Bedarf segmentieren."""
        working_geometry = geometry

        try:
            if QgsWkbTypes.isCurvedType(working_geometry.wkbType()):
                working_geometry = working_geometry.segmentize()
        except Exception:
            pass

        try:
            if working_geometry.isMultipart():
                return working_geometry.asMultiPolyline()

            line = working_geometry.asPolyline()
            if line:
                return [line]
        except Exception:
            pass

        return []

    # ------------------------------------------------------------------
    # Beschriftung
    # ------------------------------------------------------------------

    def enable_3d_labels(self, vector_layer, field_name):
        """Beschriftung auf die zuletzt berechnete Methodenspalte umstellen."""
        expression = f'format_number("{field_name}", 2) || \' m\''
        self._set_label_expression(vector_layer, expression)
