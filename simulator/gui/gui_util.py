import re
from typing import Union
import qtawesome as qta
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel


def icon_label(icon: Union[str, QIcon], text: str, color: str = None):
    widget = QWidget()
    layout = QHBoxLayout(widget)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)

    icon_lbl = QLabel()
    if isinstance(icon, QIcon):
        pixmap = icon.pixmap(16, 16)
    else:
        pixmap = qta.icon(icon, color=color).pixmap(16, 16) if color is not None else qta.icon(icon).pixmap(16, 16)

    icon_lbl.setPixmap(pixmap)
    layout.addWidget(icon_lbl)
    layout.addWidget(QLabel(text))
    layout.addStretch()
    return widget


def find_relevant_icon(name: str):
    upper = name.upper()
    if re.match("CRA", upper):
        return "mdi.head-cog"
    elif re.match("IHSA", upper):
        return "mdi.shield-alert"
    elif re.match("ASA", upper):
        return "mdi.bus-clock"
    else:
        return "mdi.account"