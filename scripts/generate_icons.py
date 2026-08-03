import os, sys, struct, io
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from PySide6.QtGui import QPixmap, QPainter, QColor, QPen, QBrush, QLinearGradient, QPainterPath
from PySide6.QtCore import Qt, QRectF, QPointF

def create_clipboard_icon(size):
    pixmap = QPixmap(size, size)
    pixmap.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    margin = max(1, size // 16)
    rect = QRectF(margin, margin, size - 2*margin, size - 2*margin)
    gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
    gradient.setColorAt(0.0, QColor('#4A90FF'))
    gradient.setColorAt(1.0, QColor('#1A5CBF'))
    painter.setBrush(QBrush(gradient))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(rect, size//5, size//5)
    body_margin_top = size * 0.28
    body_margin = size * 0.18
    body_rect = QRectF(body_margin, body_margin_top, size - 2*body_margin, size - body_margin_top - body_margin)
    painter.setBrush(QBrush(QColor(255, 255, 255, 230)))
    painter.drawRoundedRect(body_rect, size//10, size//10)
    clip_top = size * 0.20
    clip_w = size * 0.24
    clip_h = size * 0.14
    clip_x = (size - clip_w) / 2
    clip_rect = QRectF(clip_x, clip_top, clip_w, clip_h)
    painter.setBrush(QBrush(QColor('#4A90FF')))
    painter.drawRoundedRect(clip_rect, size//12, size//12)
    line_margin = size * 0.30
    line_y_start = size * 0.42
    line_spacing = size * 0.12
    pen = QPen(QColor('#999999'), max(1, size * 0.03))
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    line_width = size - 2*line_margin
    for i in range(3):
        y = line_y_start + i * line_spacing
        painter.drawLine(QPointF(line_margin, y), QPointF(line_margin + line_width, y))
    pen = QPen(QColor('#34C759'), max(1, size * 0.06))
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    check_path = QPainterPath()
    cx, cy = size * 0.55, size * 0.60
    check_path.moveTo(cx - size*0.10, cy)
    check_path.lineTo(cx - size*0.02, cy + size*0.08)
    check_path.lineTo(cx + size*0.12, cy - size*0.06)
    painter.drawPath(check_path)
    painter.end()
    return pixmap

def main():
    base_dir = os.path.join(os.path.dirname(__file__), '..', 'resources', 'icons')
    os.makedirs(base_dir, exist_ok=True)
    sizes = [16, 24, 32, 48, 64, 128, 256]
    for s in sizes:
        icon = create_clipboard_icon(s)
        icon.save(os.path.join(base_dir, f'clipmind_{s}.png'))
    png_buffers = []
    for s in [16, 32, 48]:
        icon = create_clipboard_icon(s)
        buf = io.BytesIO()
        icon.save(buf, 'PNG')
        png_buffers.append(buf.getvalue())
    num_entries = len(png_buffers)
    ico_header = struct.pack('<HHH', 0, 1, num_entries)
    entry_size = 16
    offset = 6 + entry_size * num_entries
    entries = b''
    for sz, buf in zip([16, 32, 48], png_buffers):
        w = sz if sz < 256 else 0
        h = sz if sz < 256 else 0
        entry = struct.pack('<BBBBHHII', w, h, 0, 0, 1, 32, len(buf), offset)
        entries += entry
        offset += len(buf)
    ico_path = os.path.join(base_dir, 'clipmind.ico')
    with open(ico_path, 'wb') as f:
        f.write(ico_header)
        f.write(entries)
        for buf in png_buffers:
            f.write(buf)
    print(f'All icons -> {base_dir}')
    print(f'ICO -> {ico_path}')

if __name__ == '__main__':
    main()
