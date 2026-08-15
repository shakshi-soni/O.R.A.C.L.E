import sys
import math
import random
from PyQt6.QtCore import Qt, QTimer, QPointF
from PyQt6.QtGui import QPainter, QColor, QPen, QRadialGradient, QBrush, QPainterPath
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout


# ---- standard icosahedron geometry (12 verts, 20 triangular faces) ----
_T = (1 + math.sqrt(5)) / 2
_RAW_VERTS = [
    (-1, _T, 0), (1, _T, 0), (-1, -_T, 0), (1, -_T, 0),
    (0, -1, _T), (0, 1, _T), (0, -1, -_T), (0, 1, -_T),
    (_T, 0, -1), (_T, 0, 1), (-_T, 0, -1), (-_T, 0, 1),
]

def _norm(v):
    length = math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2)
    return (v[0] / length, v[1] / length, v[2] / length)

_VERTS = [_norm(v) for v in _RAW_VERTS]

_FACES = [
    (0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11),
    (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8),
    (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9),
    (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1),
]

_EDGES = set()
for f in _FACES:
    for i in range(3):
        a, b = f[i], f[(i + 1) % 3]
        _EDGES.add((min(a, b), max(a, b)))
_EDGES = list(_EDGES)


def _subdivide(verts, faces, levels=2):
    verts = list(verts)
    faces = list(faces)
    cache = {}

    def midpoint(i1, i2):
        key = (min(i1, i2), max(i1, i2))
        if key in cache:
            return cache[key]
        v1, v2 = verts[i1], verts[i2]
        mid = _norm(((v1[0] + v2[0]) / 2, (v1[1] + v2[1]) / 2, (v1[2] + v2[2]) / 2))
        verts.append(mid)
        idx = len(verts) - 1
        cache[key] = idx
        return idx

    for _ in range(levels):
        new_faces = []
        cache.clear()
        for (a, b, c) in faces:
            ab = midpoint(a, b)
            bc = midpoint(b, c)
            ca = midpoint(c, a)
            new_faces.extend([
                (a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)
            ])
        faces = new_faces
    return verts, faces


_VERTS, _FACES = _subdivide(_VERTS, _FACES, levels=2)

_EDGES = set()
for f in _FACES:
    for i in range(3):
        a, b = f[i], f[(i + 1) % 3]
        _EDGES.add((min(a, b), max(a, b)))
_EDGES = list(_EDGES)


class OracleOrb(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.t = 0.0
        self.setMinimumSize(400, 500)
        self.setStyleSheet("background-color: black;")

        self.dust = []
        for _ in range(260):
            a = random.uniform(0, 360)
            offset = random.gauss(0, 14)  # tight cluster around the rim itself
            self.dust.append([
                a,
                offset,
                random.uniform(0.5, 1.5),
                random.uniform(0.2, 1.0),
                random.uniform(0.02, 0.12),
                random.uniform(0, 6.28),
            ])

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(30)

    def tick(self):
        self.t += 0.02
        self.update()

    def _rotate(self, v, ay, ax):
        x, y, z = v
        cz, sz = math.cos(ay), math.sin(ay)
        x, z = x * cz - z * sz, x * sz + z * cz
        cx_, sx_ = math.cos(ax), math.sin(ax)
        y, z = y * cx_ - z * sx_, y * sx_ + z * cx_
        return (x, y, z)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(0, 0, 0))

        cx = self.width() / 2
        cy = self.height() / 2 + 10
        base_r = min(self.width(), self.height()) * 0.27

        glow = QRadialGradient(cx - base_r * 1.6, cy + base_r * 2.0, base_r * 4.2)
        glow.setColorAt(0.0, QColor(10, 130, 125, 55))
        glow.setColorAt(0.5, QColor(5, 70, 70, 25))
        glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(glow))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(cx - base_r * 1.6, cy + base_r * 2.0), base_r * 4.2, base_r * 4.2)

        centered_glow = QRadialGradient(cx, cy, base_r * 2.0)
        centered_glow.setColorAt(0.0, QColor(60, 220, 210, 70))
        centered_glow.setColorAt(0.6, QColor(10, 120, 115, 25))
        centered_glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(centered_glow))
        painter.drawEllipse(QPointF(cx, cy), base_r * 2.0, base_r * 2.0)

        lobes = 11
        n = lobes * 6
        pts = []
        for i in range(n + 1):
            a = (2 * math.pi / n) * i
            lobe_wave = math.cos(a * lobes) * 0.045
            micro = math.sin(a * lobes * 3 + self.t * 0.1) * 0.008
            rad = base_r * (1.78 + lobe_wave + micro)
            pts.append(QPointF(cx + rad * math.cos(a), cy + rad * math.sin(a)))

        panel_path = QPainterPath()
        panel_path.moveTo(pts[0])
        for i in range(1, len(pts) - 1):
            mid = QPointF((pts[i].x() + pts[i + 1].x()) / 2, (pts[i].y() + pts[i + 1].y()) / 2)
            panel_path.quadTo(pts[i], mid)
        panel_path.closeSubpath()

        panel_fill = QRadialGradient(cx, cy, base_r * 1.85)
        panel_fill.setColorAt(0.0, QColor(10, 90, 90, 55))
        panel_fill.setColorAt(0.75, QColor(15, 130, 130, 50))
        panel_fill.setColorAt(1.0, QColor(0, 40, 45, 0))
        painter.setBrush(QBrush(panel_fill))
        painter.setPen(QPen(QColor(90, 230, 220, 150), 2))
        painter.drawPath(panel_path)

        # dark solid ring band between the shell edge and the segment dial
        band_outer = base_r * 1.5
        band_inner = base_r * 1.32
        band_path = QPainterPath()
        band_path.addEllipse(QPointF(cx, cy), band_outer, band_outer)
        inner_hole = QPainterPath()
        inner_hole.addEllipse(QPointF(cx, cy), band_inner, band_inner)
        band_path = band_path.subtracted(inner_hole)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(6, 45, 48, 190)))
        painter.drawPath(band_path)

        for d in self.dust:
            a, offset, size, brightness, drift, phase = d
            arad = math.radians(a + self.t * drift * 6)
            lobe_wave = math.cos(arad * lobes) * 0.045
            micro = math.sin(arad * lobes * 3 + self.t * 0.1) * 0.008
            edge_r = base_r * (1.78 + lobe_wave + micro)
            jitter = math.sin(self.t * 2 + phase) * 2
            rr = edge_r + offset + jitter
            x = cx + rr * math.cos(arad)
            y = cy + rr * math.sin(arad)
            fade = max(0.0, 1.0 - abs(offset) / 40)
            alpha = int(235 * brightness * (0.25 + 0.75 * fade))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(160, 255, 245, alpha)))
            painter.drawRect(int(x), int(y), max(1, int(size)), max(1, int(size)))

        pen = QPen(QColor(70, 200, 190, 90), 1)
        pen.setStyle(Qt.PenStyle.DashLine)
        pen.setDashPattern([1, 3])
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        vec_r = base_r * 1.42
        painter.drawEllipse(QPointF(cx, cy), vec_r, vec_r)

        seg_r = base_r * 1.18
        seg_count = 26
        for i in range(seg_count):
            a0 = (360 / seg_count) * i + self.t * 4
            span = (360 / seg_count) * 0.62
            shade = 200 if i % 2 == 0 else 150
            pen = QPen(QColor(20, 150 + (i % 3) * 8, 145, shade + 35), base_r * 0.16)
            pen.setCapStyle(Qt.PenCapStyle.FlatCap)
            painter.setPen(pen)
            painter.drawArc(
                int(cx - seg_r), int(cy - seg_r), int(seg_r * 2), int(seg_r * 2),
                int(a0 * 16), int(span * 16)
            )

        painter.setPen(QPen(QColor(225, 255, 253, 235), 2.4))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        halo_r = base_r * 0.98
        painter.drawEllipse(QPointF(cx, cy), halo_r, halo_r)

        # glossy highlight crescent on the halo ring
        painter.setPen(QPen(QColor(255, 255, 255, 220), 3.5))
        painter.drawArc(
            int(cx - halo_r), int(cy - halo_r), int(halo_r * 2), int(halo_r * 2),
            int(105 * 16), int(35 * 16)
        )

        sphere_glow = QRadialGradient(cx, cy, base_r * 0.95)
        sphere_glow.setColorAt(0.0, QColor(160, 255, 248, 150))
        sphere_glow.setColorAt(0.55, QColor(20, 170, 160, 70))
        sphere_glow.setColorAt(1.0, QColor(0, 60, 60, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(sphere_glow))
        painter.drawEllipse(QPointF(cx, cy), base_r * 0.95, base_r * 0.95)

        sphere_r = base_r * 0.62
        focal = sphere_r * 3.2
        ay = self.t * 0.5
        ax = 0.35 + math.sin(self.t * 0.15) * 0.1

        projected = []
        for v in _VERTS:
            rx, ry, rz = self._rotate(v, ay, ax)
            scale = focal / (focal + rz * sphere_r)
            px = cx + rx * sphere_r * scale
            py = cy + ry * sphere_r * scale
            projected.append((px, py, rz))

        edges_sorted = sorted(_EDGES, key=lambda e: (projected[e[0]][2] + projected[e[1]][2]))
        for (i, j) in edges_sorted:
            x1, y1, z1 = projected[i]
            x2, y2, z2 = projected[j]
            depth = (z1 + z2) / 2
            brightness = 0.35 + 0.65 * ((depth + 1) / 2)
            alpha = int(235 * brightness)
            width = 0.8 + 1.1 * ((depth + 1) / 2)
            painter.setPen(QPen(QColor(235, 255, 253, alpha), width))
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

        for (x, y, z) in projected:
            brightness = 0.4 + 0.6 * ((z + 1) / 2)
            node_r = 2.0 + 1.4 * ((z + 1) / 2)
            glow_col = QColor(190, 255, 250, int(200 * brightness))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(glow_col))
            painter.drawEllipse(QPointF(x, y), node_r, node_r)

        painter.end()


class OracleWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("O.R.A.C.L.E")
        self.setStyleSheet("background-color: black;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.orb = OracleOrb(self)
        layout.addWidget(self.orb)
        self.resize(550, 550)


def run_ui():
    app = QApplication(sys.argv)
    win = OracleWindow()
    win.show()
    app.exec()


if __name__ == "__main__":
    run_ui()