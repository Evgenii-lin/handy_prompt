"""QDark theme stylesheet."""

DARK_THEME = """
/* === GLOBAL COLORS === */
QWidget {
    background-color: #1e1e1e;
    color: #e0e0e0;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 14px;
}

QMainWindow {
    background-color: #1e1e1e;
}

QToolTip {
    color: #e0e0e0;
    background-color: #424242;
    border: 1px solid #555555;
    border-radius: 3px;
    padding: 5px;
    font-size: 12px;
}

QLabel {
    color: #e0e0e0;
    background-color: transparent;
    padding: 2px;
}

QLabel[title] {
    color: #ffffff;
    font-size: 16px;
    font-weight: bold;
}

QLabel#field_label {
    color: #e0e0e0;
    font-weight: bold;
    font-size: 14px;
}

QPushButton {
    background-color: #3d3d3d;
    color: #e0e0e0;
    border: 1px solid #555555;
    border-radius: 5px;
    padding: 10px 20px;
    min-height: 35px;
    font-size: 14px;
}

QPushButton:hover {
    background-color: #4a4a4a;
    border-color: #666666;
}

QPushButton:pressed {
    background-color: #303030;
}

QPushButton:disabled {
    background-color: #2a2a2a;
    color: #757575;
    border-color: #444444;
}

QPushButton#gen_button {
    background-color: #2e7d32;
    color: white;
    border: none;
}
QPushButton#gen_button:hover { background-color: #388e3c; }
QPushButton#gen_button:disabled { background-color: #1b5e20; color: #757575; }

QPushButton#save_button {
    background-color: #1565c0;
    color: white;
    border: none;
}
QPushButton#save_button:hover { background-color: #1976d2; }

QPushButton#add_button {
    background-color: #2e7d32;
    color: white;
    border: none;
}
QPushButton#add_button:hover { background-color: #388e3c; }

QPushButton#edit_button {
    background-color: #f57c00;
    color: white;
    border: none;
}
QPushButton#edit_button:hover { background-color: #ff8f00; }

QPushButton#del_button {
    background-color: #c62828;
    color: white;
    border: none;
}
QPushButton#del_button:hover { background-color: #d32f2f; }

QPushButton#copy_button {
    background-color: #512da8;
    color: white;
    border: none;
}
QPushButton#copy_button:hover { background-color: #673ab7; }

QPushButton#back_button {
    background-color: #616161;
    color: white;
    border: none;
}
QPushButton#back_button:hover { background-color: #757575; }

QLabel#status_label {
    color: #80cbc4;
    padding-left: 10px;
    font-style: italic;
}

QTextEdit {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border: 1px solid #424242;
    border-radius: 5px;
    padding: 10px;
    selection-background-color: #3d5afe;
    selection-color: white;
}
QTextEdit:focus { border: 1px solid #3d5afe; }
QTextEdit#input_field { padding: 8px 10px; }
QTextEdit#output_display { min-height: 200px; }

QComboBox {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border: 1px solid #424242;
    border-radius: 5px;
    padding: 8px 15px;
    min-width: 150px;
}
QComboBox:hover { border-color: #555555; }
QComboBox:disabled { background-color: #2a2a2a; color: #757575; border-color: #444444; }
QComboBox::drop-down { border: none; width: 30px; padding-right: 5px; }
QComboBox QAbstractItemView {
    background-color: #333333;
    color: #e0e0e0;
    border: 1px solid #424242;
    border-radius: 5px;
    selection-background-color: #3d5afe;
    outline: none;
    font-size: 14px;
    min-height: 25px;
}
QComboBox QAbstractItemView::item { padding: 5px 10px; }
QComboBox QAbstractItemView::item:hover { background-color: #424242; }
QComboBox QAbstractItemView::item:selected { background-color: #3d5afe; color: white; }

QScrollBar:vertical {
    background-color: #2d2d2d;
    width: 12px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background-color: #4a4a4a;
    min-height: 20px;
    border-radius: 5px;
    margin: 2px;
}
QScrollBar::handle:vertical:hover { background-color: #5a5a5a; }
QScrollBar::handle:vertical:pressed { background-color: #3d5afe; }
QScrollBar::add-line:vertical { height: 0px; }
QScrollBar::sub-line:vertical { height: 0px; }
QScrollBar:horizontal {
    background-color: #2d2d2d;
    height: 12px;
    margin: 0px;
}
QScrollBar::handle:horizontal {
    background-color: #4a4a4a;
    min-width: 20px;
    border-radius: 5px;
    margin: 2px;
}
QScrollBar::handle:horizontal:hover { background-color: #5a5a5a; }

QProgressBar {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border: 1px solid #424242;
    border-radius: 5px;
    text-align: center;
    font-size: 12px;
    padding: 0px;
}
QProgressBar::chunk {
    background-color: #4CAF50;
    border-radius: 4px;
}

QTabWidget::pane {
    border: 1px solid #424242;
    border-radius: 5px;
    background-color: #2d2d2d;
}
QTabBar::tab {
    background-color: #2d2d2d;
    color: #e0e0e0;
    padding: 10px 20px;
    border: none;
    border-bottom: 2px solid transparent;
}
QTabBar::tab:selected {
    background-color: #333333;
    border-bottom: 2px solid #4CAF50;
}
QTabBar::tab:!selected { background-color: #2d2d2d; }

QMessageBox {
    background-color: #2d2d2d;
    color: #e0e0e0;
}
QMessageBox QLabel { color: #e0e0e0; }
QMessageBox QPushButton {
    background-color: #3d3d3d;
    color: #e0e0e0;
    border: 1px solid #555555;
    border-radius: 5px;
    padding: 8px 20px;
    min-width: 80px;
}
QMessageBox QPushButton:hover { background-color: #4a4a4a; }

QLineEdit {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border: 1px solid #424242;
    border-radius: 5px;
    padding: 8px;
    selection-background-color: #3d5afe;
}
QLineEdit:focus { border: 1px solid #3d5afe; }
"""
