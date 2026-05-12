from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QPainterPath, QFont, QPen
from PyQt6.QtCore import Qt, QRectF, QPointF


def make_icon(size: int = 256) -> QIcon:
    """Генерирует иконку приложения программно."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    p = QPainter(pixmap)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    s = size
    r = s * 0.18  # радиус скругления

    # ── Фон: тёмно-синий прямоугольник ──────────────────────────────────────
    bg_path = QPainterPath()
    bg_path.addRoundedRect(QRectF(0, 0, s, s), r, r)
    p.fillPath(bg_path, QColor("#1E2A3A"))

    # ── Лист документа (белый, с загнутым углом) ─────────────────────────────
    lx = s * 0.22   # левый край листа
    ty = s * 0.12   # верхний край
    rx = s * 0.78   # правый край
    by = s * 0.76   # нижний край
    fold = s * 0.17  # размер загнутого угла

    doc = QPainterPath()
    doc.moveTo(lx, ty)
    doc.lineTo(rx - fold, ty)
    doc.lineTo(rx, ty + fold)
    doc.lineTo(rx, by)
    doc.lineTo(lx, by)
    doc.closeSubpath()
    p.fillPath(doc, QColor("#FFFFFF"))

    # Загнутый угол — треугольник чуть темнее
    corner = QPainterPath()
    corner.moveTo(rx - fold, ty)
    corner.lineTo(rx, ty + fold)
    corner.lineTo(rx - fold, ty + fold)
    corner.closeSubpath()
    p.fillPath(corner, QColor("#CBD5E0"))

    # ── Строки текста на листе ────────────────────────────────────────────────
    line_color = QColor("#A0AEC0")
    line_w = max(1, int(s * 0.025))
    p.setPen(QPen(line_color, line_w, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))

    line_x1 = s * 0.30
    line_x2 = s * 0.70
    for frac in [0.35, 0.44, 0.53]:
        y = s * frac
        p.drawLine(QPointF(line_x1, y), QPointF(line_x2, y))

    # Последняя строка — короче
    p.drawLine(QPointF(line_x1, s * 0.62), QPointF(s * 0.56, s * 0.62))

    # ── Акцентный круг с галочкой (выполнено) ────────────────────────────────
    cx = s * 0.67
    cy = s * 0.70
    cr = s * 0.18

    # Тень круга
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(0, 0, 0, 40))
    p.drawEllipse(QPointF(cx + s * 0.01, cy + s * 0.01), cr, cr)

    # Круг
    p.setBrush(QColor("#3B82F6"))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(QPointF(cx, cy), cr, cr)

    # Галочка
    pen = QPen(QColor("#FFFFFF"), max(2, int(s * 0.05)),
               Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    check = QPainterPath()
    check.moveTo(cx - cr * 0.45, cy)
    check.lineTo(cx - cr * 0.05, cy + cr * 0.42)
    check.lineTo(cx + cr * 0.50, cy - cr * 0.38)
    p.drawPath(check)

    p.end()

    icon = QIcon()
    for sz in [16, 24, 32, 48, 64, 128, 256]:
        icon.addPixmap(pixmap.scaled(
            sz, sz,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        ))
    return icon
