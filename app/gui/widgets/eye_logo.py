"""
Blinking eye logo widget for the welcome screen.
"""
from __future__ import annotations

import random

from PyQt6.QtCore import (
    Qt,
    QTimer,
    pyqtProperty,
    QPropertyAnimation,
    QEasingCurve,
    QSequentialAnimationGroup,
    QRectF,
)
from PyQt6.QtGui import (
    QPainter,
    QColor,
    QPen,
    QBrush,
    QPainterPath,
    QRadialGradient,
)
from PyQt6.QtWidgets import QWidget, QSizePolicy


class BlinkingEyeWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._blink = 0.0

        self.setMinimumSize(220, 120)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        self._blink_group = QSequentialAnimationGroup(self)
        close_anim = QPropertyAnimation(self, b"blink")
        close_anim.setStartValue(0.0)
        close_anim.setEndValue(1.0)
        close_anim.setDuration(120)
        close_anim.setEasingCurve(QEasingCurve.Type.InQuad)

        open_anim = QPropertyAnimation(self, b"blink")
        open_anim.setStartValue(1.0)
        open_anim.setEndValue(0.0)
        open_anim.setDuration(160)
        open_anim.setEasingCurve(QEasingCurve.Type.OutQuad)

        self._blink_group.addAnimation(close_anim)
        self._blink_group.addAnimation(open_anim)
        self._blink_group.finished.connect(self._schedule_blink)

        self._schedule_blink()

    def _schedule_blink(self):
        delay = random.randint(1200, 2800)
        QTimer.singleShot(delay, self._blink_group.start)

    def get_blink(self) -> float:
        return self._blink

    def set_blink(self, value: float) -> None:
        self._blink = max(0.0, min(1.0, float(value)))
        self.update()

    blink = pyqtProperty(float, fget=get_blink, fset=set_blink)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        w = self.width()
        h = self.height()
        cx = w * 0.5
        cy = h * 0.55

        eye_w = min(w * 0.78, h * 2.2)
        eye_h = min(h * 0.45, w * 0.28)
        open_h = max(eye_h * (1.0 - 0.85 * self._blink), eye_h * 0.08)

        left = cx - eye_w * 0.5
        right = cx + eye_w * 0.5
        top = cy - open_h * 0.5
        bottom = cy + open_h * 0.5

        outline_color = QColor("#7b8698")
        sclera_color = QColor("#ffffff")

        outline_pen = QPen(outline_color, 4)
        painter.setPen(outline_pen)
        painter.setBrush(QBrush(sclera_color))

        eye_path = QPainterPath()
        eye_path.moveTo(left, cy)
        eye_path.quadTo(cx, top, right, cy)
        eye_path.quadTo(cx, bottom, left, cy)
        painter.drawPath(eye_path)

        painter.save()
        painter.setClipPath(eye_path)

        iris_r = min(eye_w * 0.13, open_h * 0.9)
        iris_center_y = cy + open_h * 0.02

        iris_grad = QRadialGradient(cx, iris_center_y, iris_r * 1.2)
        iris_grad.setColorAt(0.0, QColor("#7fb3ff"))
        iris_grad.setColorAt(0.45, QColor("#2f6fff"))
        iris_grad.setColorAt(1.0, QColor("#0f2a66"))

        iris_brush = QBrush(iris_grad)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(iris_brush)
        iris_alpha = 1.0 - min(self._blink * 1.1, 1.0)
        painter.setOpacity(iris_alpha)
        painter.drawEllipse(QRectF(cx - iris_r, iris_center_y - iris_r, iris_r * 2, iris_r * 2))

        pupil_r = iris_r * 0.35
        painter.setOpacity(iris_alpha)
        painter.setBrush(QColor("#0b1220"))
        painter.drawEllipse(QRectF(cx - pupil_r, iris_center_y - pupil_r, pupil_r * 2, pupil_r * 2))

        highlight_r = pupil_r * 0.45
        painter.setBrush(QColor(255, 255, 255, 210))
        painter.drawEllipse(QRectF(cx - pupil_r * 0.6, iris_center_y - pupil_r * 0.6, highlight_r, highlight_r))
        painter.restore()

        if self._blink < 0.8:
            lash_pen = QPen(QColor("#2d3542"), 3)
            painter.setPen(lash_pen)
            lash_len = eye_h * 0.3
            for i, offset in enumerate([-0.28, -0.14, 0.0, 0.14, 0.28]):
                x = cx + (eye_w * 0.45 * offset)
                painter.drawLine(int(x), int(top - lash_len * 0.1), int(x), int(top - lash_len))

        painter.end()
