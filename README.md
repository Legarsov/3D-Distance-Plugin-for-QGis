# 3D Distance – QGIS Plugin

## Deutsch

### Übersicht

**3D Distance** ist ein QGIS-Plugin zur Berechnung und Beschriftung dreidimensionaler Linienlängen auf Grundlage eines digitalen Geländemodells (DEM).

Das Plugin unterstützt drei unterschiedliche Berechnungsmethoden:

- **Kartesisch**
- **Ellipsoidisch**
- **Geozentrisch / ECEF**

Bei Linien mit mehreren Stützpunkten wird die 3D-Länge jedes einzelnen Segments berechnet und anschließend zur Gesamtlänge der Linie addiert.

Zusätzlich können geografische und magnetische Azimute in **Grad** oder **Gon** berechnet und als Attribute gespeichert werden. Die magnetische Deklination wird offline und CRS-unabhängig mit dem **World Magnetic Model 2025 (WMM2025)** bestimmt.

---

### Funktionen

#### 3D-Längenberechnung

**Kartesisch**

Die 3D-Distanz wird aus den kartesischen Koordinaten und der Höhendifferenz berechnet:

```text
d3D = sqrt(Δx² + Δy² + Δz²)
```

Diese Methode eignet sich besonders für lokale Berechnungen in geeigneten projizierten Koordinatensystemen.

**Ellipsoidisch**

Die horizontale Distanz wird ellipsoidisch bestimmt und anschließend mit der Höhendifferenz kombiniert:

```text
d3D = sqrt(d_ellipsoid² + ΔH²)
```

Diese Methode ist weitgehend unabhängig vom verwendeten projizierten CRS und eignet sich sehr gut für typische GIS-Anwendungen.

**Geozentrisch / ECEF**

Die Punkte werden in geozentrische Koordinaten umgerechnet und die räumliche Distanz berechnet:

```text
d3D = sqrt(ΔX² + ΔY² + ΔZ²)
```

Diese Methode stellt die geometrisch sauberste räumliche Luftlinienberechnung dar.

---

### Azimutberechnung

Das Plugin kann den Azimut einer Linie zusätzlich berechnen und in der Attributtabelle speichern.

Unterstützt werden:

- geografischer Azimut in **Grad**
- geografischer Azimut in **Gon**
- magnetische Deklination in **Grad**
- magnetische Deklination in **Gon**
- magnetischer Azimut unter Berücksichtigung der Deklination

Die magnetische Deklination wird mit dem im Plugin hinterlegten **WMM2025** berechnet. Dafür ist keine Internetverbindung erforderlich.

Die Berechnung erfolgt CRS-unabhängig, da die benötigten Positionen intern nach WGS84 transformiert werden.

---

### Beschriftung

Die berechnete 3D-Länge kann direkt als Linienbeschriftung dargestellt werden.

Optional kann zusätzlich der

- geografische Azimut oder
- magnetische Azimut

angezeigt werden.

Über die Radio-Buttons kann gewählt werden, ob der Azimut in **Grad** oder **Gon** dargestellt wird.

Alle vom Plugin erzeugten Beschriftungen werden in der Farbe

```text
#ffff00
```

dargestellt.

Die Schaltfläche **„Beschriftung zurücksetzen – Reset label“** deaktiviert die Beschriftung, löscht jedoch keine berechneten Attributfelder.

---

### Attributfelder

Für die verschiedenen Berechnungen werden getrennte Attributfelder angelegt, damit Ergebnisse verschiedener Methoden parallel erhalten bleiben.

Beispiele:

```text
L3D_Kart
L3D_Elli
L3D_ECEF
Azi_Grad
Azi_Gon
Dekl_Grad
Dekl_Gon
```

Je nach Berechnungsmethode können weitere Felder verwendet werden.

---

### Bedienung

1. Plugin in QGIS öffnen.
2. Einen **DEM-Rasterlayer** auswählen.
3. Einen **Vektorlayer mit Liniengeometrie** auswählen.
4. Eine Methode für die 3D-Berechnung auswählen:
   - Kartesisch
   - Ellipsoidisch
   - Geozentrisch / ECEF
5. Mit **OK** die 3D-Länge berechnen.
6. Optional:
   - Azimut in Grad berechnen
   - Azimut in Gon berechnen
   - Grad oder Gon für die Beschriftung auswählen
   - geografischen oder magnetischen Azimut zur Beschriftung hinzufügen
7. Mit **Aktualisieren – Refresh** die Layerlisten neu einlesen, ohne das Pluginfenster neu öffnen zu müssen.
8. Mit **Beschriftung zurücksetzen – Reset label** die aktuelle Beschriftung deaktivieren.

---

### Hinweise

- Für die kartesische Berechnung sollte ein geeignetes projiziertes CRS mit metrischen Einheiten verwendet werden.
- Die ellipsoidische und geozentrische Berechnung sind gegenüber dem verwendeten Karten-CRS robuster.
- DEM-Höhen werden an den Stützpunkten der Linie abgefragt.
- Bei Linien mit mehreren Segmenten werden alle Segmentlängen summiert.
- Die magnetische Deklination wird offline mit WMM2025 berechnet.
- Für streng geodätische ECEF-Berechnungen ist zu beachten, dass viele DEMs orthometrische Höhen liefern, während ECEF mathematisch ellipsoidische Höhen verwendet.

---

### Anforderungen

- QGIS 3.x
- Python 3
- Digitales Geländemodell als Rasterlayer
- Linien-Vektorlayer

---

### Lizenz

Dieses Plugin wurde mit dem QGIS Plugin Builder erstellt und steht unter der in den Plugin-Dateien angegebenen Lizenz.

---

## English

### Overview

**3D Distance** is a QGIS plugin for calculating and labeling three-dimensional line lengths based on a digital elevation model (DEM).

The plugin supports three calculation methods:

- **Cartesian**
- **Ellipsoidal**
- **Geocentric / ECEF**

For lines containing multiple vertices, the 3D length of each individual segment is calculated and then summed to obtain the total line length.

In addition, geographic and magnetic azimuths can be calculated in **degrees** or **gon** and stored as attributes. Magnetic declination is calculated offline and independently of the project CRS using the **World Magnetic Model 2025 (WMM2025)**.

---

### Features

#### 3D distance calculation

**Cartesian**

The 3D distance is calculated from Cartesian coordinates and elevation difference:

```text
d3D = sqrt(Δx² + Δy² + Δz²)
```

This method is especially suitable for local calculations in an appropriate projected coordinate reference system.

**Ellipsoidal**

The horizontal distance is calculated on the ellipsoid and then combined with the height difference:

```text
d3D = sqrt(d_ellipsoid² + ΔH²)
```

This method is largely independent of the selected projected CRS and is well suited for typical GIS applications.

**Geocentric / ECEF**

The points are transformed into geocentric coordinates and the spatial distance is calculated:

```text
d3D = sqrt(ΔX² + ΔY² + ΔZ²)
```

This method provides the geometrically cleanest spatial straight-line distance.

---

### Azimuth calculation

The plugin can also calculate the azimuth of a line and store it in the attribute table.

Supported values include:

- geographic azimuth in **degrees**
- geographic azimuth in **gon**
- magnetic declination in **degrees**
- magnetic declination in **gon**
- magnetic azimuth including declination correction

Magnetic declination is calculated using the **WMM2025** model embedded in the plugin. No internet connection is required.

The calculation is CRS-independent because the required positions are internally transformed to WGS84.

---

### Labeling

The calculated 3D length can be displayed directly as a line label.

Optionally, the label can also include either the

- geographic azimuth or
- magnetic azimuth.

Radio buttons allow the user to select whether the azimuth is displayed in **degrees** or **gon**.

All labels created by the plugin are displayed using the color

```text
#ffff00
```

The **“Reset label”** button disables the labeling without deleting any calculated attribute fields.

---

### Attribute fields

Separate attribute fields are created for the different calculation methods so that results from different methods can be stored simultaneously.

Examples:

```text
L3D_Kart
L3D_Elli
L3D_ECEF
Azi_Grad
Azi_Gon
Dekl_Grad
Dekl_Gon
```

Additional fields may be used depending on the selected calculation.

---

### Usage

1. Open the plugin in QGIS.
2. Select a **DEM raster layer**.
3. Select a **vector layer with line geometry**.
4. Choose a 3D calculation method:
   - Cartesian
   - Ellipsoidal
   - Geocentric / ECEF
5. Press **OK** to calculate the 3D length.
6. Optionally:
   - calculate azimuth in degrees
   - calculate azimuth in gon
   - select degrees or gon for labeling
   - add geographic or magnetic azimuth to the label
7. Use **Refresh** to reload the available layer lists without reopening the plugin window.
8. Use **Reset label** to disable the current labeling.

---

### Notes

- The Cartesian method should be used with an appropriate projected CRS using metric units.
- Ellipsoidal and geocentric calculations are more robust with respect to the selected map CRS.
- DEM elevations are sampled at the vertices of the line.
- For multi-segment lines, all individual segment lengths are summed.
- Magnetic declination is calculated offline using WMM2025.
- For strictly geodetic ECEF calculations, note that many DEMs provide orthometric heights, while ECEF mathematically uses ellipsoidal heights.

---

### Requirements

- QGIS 3.x
- Python 3
- Digital elevation model as raster layer
- Vector line layer

---

### License

This plugin was created with the QGIS Plugin Builder and is distributed under the license specified in the plugin files.
