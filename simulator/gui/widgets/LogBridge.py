from PyQt6.QtCore import QObject, pyqtSignal

class LogBridge(QObject):
    """
    The log bridge allows for you to emit log messages from any part of the application, to the GUI
    """
    log_line = pyqtSignal(str, str)  # level, message
