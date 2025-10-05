import os

# Prefer the PySide6 backend when QtPy resolves the Qt binding.
os.environ.setdefault("QT_API", "pyside2")
