import sys
import os
import json
import winreg
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QLineEdit, QPushButton, QComboBox, QScrollArea, QFrame,
    QStackedWidget, QFileDialog, QMessageBox, QSpacerItem, QSizePolicy, QToolTip
)
from PyQt6.QtCore import (
    Qt, QPropertyAnimation, pyqtProperty, QEasingCurve, QTimer, QCoreApplication,
    pyqtSignal, QObject
)
from PyQt6.QtGui import QColor, QPainter, QBrush, QPen, QFont, QCursor

# モダンなQSSスタイル
MODERN_QSS = """
QMainWindow {
    background-color: #f5f5f7;
}
QToolTip {
    color: #4a4a4a;
    background-color: #ffffff;
    border: 1px solid #d1d1d6;
    border-radius: 6px;
    padding: 8px;
    font-size: 13px;
    /* Drop shadow effect is handled by OS for tooltips, but the styling ensures clarity */
}
QFrame#Card {
    background-color: #ffffff;
    border-radius: 12px;
    border: 1px solid #e5e5ea;
}
QLabel {
    color: #1d1d1f;
    font-size: 14px;
}
QLabel#Title {
    font-size: 24px;
    font-weight: bold;
    color: #1d1d1f;
}
QLabel#StepTitle {
    font-size: 14px;
    font-weight: bold;
    color: #ffffff;
    background-color: #007aff;
    border-radius: 10px;
    padding: 4px 10px;
}
QLineEdit {
    background-color: #f2f2f7;
    border: 1px solid #e5e5ea;
    border-radius: 8px;
    padding: 8px;
    font-size: 14px;
    color: #1d1d1f;
}
QLineEdit:focus {
    border: 2px solid #007aff;
    background-color: #ffffff;
}
QPushButton {
    background-color: #ffffff;
    border: 1px solid #d1d1d6;
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 14px;
    font-weight: 500;
    color: #1d1d1f;
}
QPushButton:hover {
    background-color: #f2f2f7;
}
QPushButton:pressed {
    background-color: #e5e5ea;
}
QPushButton#PrimaryButton {
    background-color: #007aff;
    border: none;
    color: #ffffff;
    font-weight: bold;
}
QPushButton#PrimaryButton:hover {
    background-color: #006ee6;
}
QPushButton#PrimaryButton:pressed {
    background-color: #005bb5;
}
QPushButton#DangerButton {
    background-color: #ff3b30;
    border: none;
    color: #ffffff;
    font-weight: bold;
}
QPushButton#DangerButton:hover {
    background-color: #ff2d20;
}
QPushButton#WarningButton {
    background-color: #ffcc00;
    border: none;
    color: #ffffff;
    font-weight: bold;
}
QPushButton#WarningButton:hover {
    background-color: #e6b800;
}
QPushButton#SidebarButton {
    text-align: left;
    background-color: transparent;
    border: none;
    border-radius: 8px;
    padding: 10px;
    color: #4a4a4a;
}
QPushButton#SidebarButton:hover {
    background-color: #e5e5ea;
}
QPushButton#SidebarButtonActive {
    text-align: left;
    background-color: #e5e5ea;
    border: none;
    border-radius: 8px;
    padding: 10px;
    color: #1d1d1f;
    font-weight: bold;
}
QComboBox {
    background-color: #f2f2f7;
    border: 1px solid #e5e5ea;
    border-radius: 8px;
    padding: 8px;
    font-size: 14px;
    color: #1d1d1f;
}
QComboBox::drop-down {
    border: none;
}
QScrollArea {
    border: none;
    background-color: transparent;
}
QScrollBar:vertical {
    border: none;
    background: #f5f5f7;
    width: 8px;
    border-radius: 4px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #c7c7cc;
    min-height: 20px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: #aeaeb2;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""

class ToggleSwitch(QWidget):
    def __init__(self, parent=None, is_checked=False):
        super().__init__(parent)
        self.setFixedSize(50, 26)
        self._checked = is_checked
        self._position = 22 if is_checked else 4
        self.animation = QPropertyAnimation(self, b"position")
        self.animation.setEasingCurve(QEasingCurve.Type.InOutSine)
        self.animation.setDuration(200)

    @pyqtProperty(float)
    def position(self):
        return self._position

    @position.setter
    def position(self, pos):
        self._position = pos
        self.update()

    def isChecked(self):
        return self._checked

    def setChecked(self, checked):
        if self._checked != checked:
            self._checked = checked
            self.animation.setEndValue(22 if checked else 4)
            self.animation.start()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setChecked(not self._checked)
            super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Background
        p.setPen(Qt.PenStyle.NoPen)
        bg_color = QColor("#34c759") if self._checked else QColor("#e5e5ea")
        p.setBrush(QBrush(bg_color))
        p.drawRoundedRect(0, 0, self.width(), self.height(), 13, 13)
        
        # Knob (with slight shadow)
        p.setBrush(QBrush(QColor("#ffffff")))
        p.setPen(QPen(QColor("#d1d1d6"), 1))
        # Add a subtle fake shadow via multiple circles
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(0, 0, 0, 30)))
        p.drawEllipse(int(self._position), 4, 18, 18)
        
        p.setBrush(QBrush(QColor("#ffffff")))
        p.drawEllipse(int(self._position), 3, 18, 18)
        p.end()

class ModernWindow(QMainWindow):
    def __init__(self, config_path, on_close_callback, monitor):
        super().__init__()
        self.config_path = config_path
        self.on_close_callback = on_close_callback
        self.monitor = monitor
        
        self.games = []
        self.launch_interval = 5
        self.kill_targets = ["なし", "なし", "なし"]
        self.run_on_startup = False
        self.auto_exit = False
        self.current_selected_index = None # None means App Settings
        
        self.load_config()
        self.init_ui()

    def load_config(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    self.games = config.get("games", [])
                    self.launch_interval = config.get("launch_interval", 5)
                    loaded_kills = config.get("kill_targets", [])
                    self.kill_targets = (loaded_kills + ["なし", "なし", "なし"])[:3]
                    self.run_on_startup = config.get("run_on_startup", False)
                    self.auto_exit = config.get("auto_exit_after_completion", False)
                if self.monitor:
                    self.monitor.auto_exit_after_completion = self.auto_exit
            except Exception as e:
                print(f"Failed to load config: {e}")

    def save_config(self):
        try:
            # fetch current app settings before saving if they are active
            try:
                self.launch_interval = int(self.interval_entry.text())
            except ValueError:
                self.launch_interval = 5
                
            self.kill_targets = [
                self.kill_combo_1.currentText(),
                self.kill_combo_2.currentText(),
                self.kill_combo_3.currentText()
            ]
            self.run_on_startup = self.startup_toggle.isChecked()
            self.auto_exit = self.auto_exit_toggle.isChecked()
            
            # Save profile values if a profile is currently open
            self.sync_current_profile_input()
            
            config_data = {
                "games": self.games,
                "launch_interval": self.launch_interval,
                "kill_targets": self.kill_targets,
                "run_on_startup": self.run_on_startup,
                "auto_exit_after_completion": self.auto_exit
            }
            
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
                
            if self.monitor:
                self.monitor.auto_exit_after_completion = self.auto_exit
                
            self.set_run_on_startup(self.run_on_startup)
            return True
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"設定の保存に失敗しました:\n{e}")
            return False

    def set_run_on_startup(self, enable):
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        app_name = "DailyGameLauncher"
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS)
            if enable:
                if getattr(sys, 'frozen', False):
                    cmd = f'"{sys.executable}" --startup'
                else:
                    base_dir = os.path.dirname(os.path.abspath(__file__))
                    main_py_path = os.path.join(base_dir, "main.py")
                    pythonw_path = sys.executable.replace("python.exe", "pythonw.exe")
                    if not os.path.exists(pythonw_path):
                        pythonw_path = sys.executable
                    cmd = f'"{pythonw_path}" "{main_py_path}" --startup'
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, cmd)
            else:
                try:
                    winreg.DeleteValue(key, app_name)
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except Exception as e:
            print(f"Failed to set startup registry: {e}")

    def init_ui(self):
        self.setWindowTitle("日課ツール 登録設定")
        self.resize(900, 650)
        self.setMinimumSize(750, 550)
        
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # --- Sidebar ---
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(260)
        self.sidebar.setStyleSheet("QFrame { background-color: #ffffff; border-right: 1px solid #e5e5ea; }")
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(20, 30, 20, 30)
        
        title = QLabel("設定メニュー")
        title.setObjectName("Title")
        sidebar_layout.addWidget(title)
        sidebar_layout.addSpacing(20)
        
        self.app_settings_btn = QPushButton("⚙ アプリ全体設定")
        self.app_settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.app_settings_btn.clicked.connect(self.show_app_settings)
        sidebar_layout.addWidget(self.app_settings_btn)
        
        sidebar_layout.addSpacing(15)
        prof_lbl = QLabel("ゲームプロファイル")
        prof_lbl.setStyleSheet("color: #8e8e93; font-size: 12px; font-weight: bold;")
        sidebar_layout.addWidget(prof_lbl)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_area.setWidget(self.scroll_content)
        sidebar_layout.addWidget(self.scroll_area)
        
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("+ 追加")
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setToolTip("新しいゲームプロファイルを追加します。")
        add_btn.clicked.connect(self.add_profile)
        self.del_btn = QPushButton("🗑 削除")
        self.del_btn.setObjectName("DangerButton")
        self.del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.del_btn.setToolTip("選択中のゲームプロファイルを削除します。")
        self.del_btn.clicked.connect(self.delete_profile)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(self.del_btn)
        sidebar_layout.addLayout(btn_layout)
        
        # --- Main Content Area ---
        self.main_content = QWidget()
        mc_layout = QVBoxLayout(self.main_content)
        mc_layout.setContentsMargins(40, 30, 40, 30)
        
        # Header
        header_layout = QHBoxLayout()
        self.content_title = QLabel("アプリ全体設定")
        self.content_title.setObjectName("Title")
        
        save_btn = QPushButton("保存して適用")
        save_btn.setObjectName("PrimaryButton")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setToolTip("設定を保存し、ランチャーへ適用します。")
        save_btn.clicked.connect(self.save_and_close)
        
        header_layout.addWidget(self.content_title)
        header_layout.addStretch()
        header_layout.addWidget(save_btn)
        mc_layout.addLayout(header_layout)
        mc_layout.addSpacing(20)
        
        # Stacked Widget
        self.stacked = QStackedWidget()
        
        self.app_settings_card = QFrame()
        self.app_settings_card.setObjectName("Card")
        self.init_app_settings(self.app_settings_card)
        self.stacked.addWidget(self.app_settings_card)
        
        self.profile_card = QFrame()
        self.profile_card.setObjectName("Card")
        self.init_profile_settings(self.profile_card)
        self.stacked.addWidget(self.profile_card)
        
        mc_layout.addWidget(self.stacked)
        
        # Assemble
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.main_content)
        
        self.refresh_sidebar()
        self.show_app_settings()

    def init_app_settings(self, container):
        layout = QVBoxLayout(container)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)
        
        # Interval
        int_layout = QHBoxLayout()
        int_lbl = QLabel("次のゲームまでの待ち時間 (秒):")
        int_lbl.setToolTip("PCのカクつきを防ぐための準備時間です。PCの性能が低い場合は長め(10秒など)に設定してください。")
        self.interval_entry = QLineEdit(str(self.launch_interval))
        self.interval_entry.setFixedWidth(80)
        int_layout.addWidget(int_lbl)
        int_layout.addWidget(self.interval_entry)
        int_layout.addStretch()
        layout.addLayout(int_layout)
        
        # Kill targets
        kill_lbl = QLabel("一緒に閉じる裏方アプリ (ゲーム終了時に閉じます):")
        kill_lbl.setToolTip("ランチャーやストアアプリなど、不要なバックグラウンドプロセスを自動でキルし、PCを軽くします。")
        layout.addWidget(kill_lbl)
        
        kill_opts = ["なし", "HoYoPlay (hoyoplay.exe)", "Steam (steam.exe)", "Epic Games (EpicGamesLauncher.exe)"]
        self.kill_combo_1 = QComboBox(); self.kill_combo_1.addItems(kill_opts); self.kill_combo_1.setCurrentText(self.kill_targets[0])
        self.kill_combo_2 = QComboBox(); self.kill_combo_2.addItems(kill_opts); self.kill_combo_2.setCurrentText(self.kill_targets[1])
        self.kill_combo_3 = QComboBox(); self.kill_combo_3.addItems(kill_opts); self.kill_combo_3.setCurrentText(self.kill_targets[2])
        
        layout.addWidget(self.kill_combo_1)
        layout.addWidget(self.kill_combo_2)
        layout.addWidget(self.kill_combo_3)
        layout.addSpacing(10)
        
        # Toggles
        start_layout = QHBoxLayout()
        self.startup_toggle = ToggleSwitch(is_checked=self.run_on_startup)
        start_lbl = QLabel("PC起動時に自動で開始する")
        start_lbl.setToolTip("Windows起動時に、タスクトレイに常駐するようになります。")
        start_layout.addWidget(self.startup_toggle)
        start_layout.addWidget(start_lbl)
        start_layout.addStretch()
        layout.addLayout(start_layout)
        
        auto_layout = QHBoxLayout()
        self.auto_exit_toggle = ToggleSwitch(is_checked=self.auto_exit)
        auto_lbl = QLabel("日課完了後にこのツールを自動終了する")
        auto_lbl.setToolTip("登録した全てのゲームを通しでプレイし終わった後、このランチャーも自ら終了します。")
        auto_layout.addWidget(self.auto_exit_toggle)
        auto_layout.addWidget(auto_lbl)
        auto_layout.addStretch()
        layout.addLayout(auto_layout)
        
        layout.addStretch()
        
        # Action Buttons
        start_routine_btn = QPushButton("▶ 日課を開始 (1番目のゲームを起動)")
        start_routine_btn.setObjectName("PrimaryButton")
        start_routine_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        start_routine_btn.clicked.connect(self.action_start_routine)
        layout.addWidget(start_routine_btn)
        
        reset_btn = QPushButton("❌ すべてのゲームをリセット")
        reset_btn.setObjectName("DangerButton")
        reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reset_btn.clicked.connect(self.action_reset_all)
        layout.addWidget(reset_btn)

    def init_profile_settings(self, container):
        layout = QVBoxLayout(container)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)
        
        # Step Label
        self.step_label = QLabel("No. 1")
        self.step_label.setObjectName("StepTitle")
        self.step_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.step_label)
        
        # Name
        name_layout = QHBoxLayout()
        name_lbl = QLabel("ゲーム表示名:")
        self.prof_name_entry = QLineEdit()
        self.prof_name_entry.textChanged.connect(self.on_profile_edit)
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(["プリセット...", "原神", "崩壊：スターレイル", "鳴潮"])
        self.preset_combo.currentTextChanged.connect(self.on_preset_selected)
        name_layout.addWidget(name_lbl)
        name_layout.addWidget(self.prof_name_entry, 1)
        name_layout.addWidget(self.preset_combo)
        layout.addLayout(name_layout)
        
        # Process
        proc_layout = QHBoxLayout()
        proc_lbl = QLabel("プロセス名 (例: Game.exe):")
        proc_lbl.setToolTip("このプロセスが立ち上がっている間は「プレイ中」と判定し、終了したら次のゲームに行きます。")
        self.prof_proc_entry = QLineEdit()
        self.prof_proc_entry.textChanged.connect(self.on_profile_edit)
        proc_layout.addWidget(proc_lbl)
        proc_layout.addWidget(self.prof_proc_entry, 1)
        layout.addLayout(proc_layout)
        
        # Path
        path_layout = QVBoxLayout()
        path_lbl = QLabel("実行ファイルパス:")
        path_lbl.setToolTip("自動検出が失敗した場合は、「参照」からゲーム本体の .exe を選んでください。")
        path_input_lyt = QHBoxLayout()
        self.prof_path_entry = QLineEdit()
        self.prof_path_entry.textChanged.connect(self.on_profile_edit)
        browse_btn = QPushButton("参照...")
        browse_btn.clicked.connect(self.browse_file)
        detect_btn = QPushButton("✨自動検出")
        detect_btn.setObjectName("WarningButton")
        detect_btn.setToolTip("レジストリや標準的なインストールパスからゲームを自動で探します。まずはゲーム表示名を入力してください。")
        detect_btn.clicked.connect(self.auto_detect)
        path_input_lyt.addWidget(self.prof_path_entry)
        path_input_lyt.addWidget(browse_btn)
        path_input_lyt.addWidget(detect_btn)
        path_layout.addWidget(path_lbl)
        path_layout.addLayout(path_input_lyt)
        layout.addLayout(path_layout)
        
        # Order Control
        order_lyt = QHBoxLayout()
        up_btn = QPushButton("↑ 順番を上げる")
        up_btn.clicked.connect(self.move_up)
        down_btn = QPushButton("↓ 順番を下げる")
        down_btn.clicked.connect(self.move_down)
        order_lyt.addWidget(up_btn)
        order_lyt.addWidget(down_btn)
        order_lyt.addStretch()
        layout.addLayout(order_lyt)
        
        # Line
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("border: 1px solid #e5e5ea;")
        layout.addWidget(line)
        
        # Launch overrides
        laun_lyt = QHBoxLayout()
        launch_btn = QPushButton("▶ このゲームを起動")
        launch_btn.setStyleSheet("background-color: #34c759; color: white; font-weight: bold; border: none;")
        launch_btn.clicked.connect(self.launch_current)
        
        self.chain_toggle = ToggleSwitch(is_checked=True)
        chain_lbl = QLabel("連続プレイモード (終了後に次のゲームへ)")
        chain_lbl.setToolTip("OFFにすると、このゲームが終了しても次のゲームを起動せずに待機状態に戻ります。")
        
        laun_lyt.addWidget(launch_btn)
        laun_lyt.addSpacing(20)
        laun_lyt.addWidget(self.chain_toggle)
        laun_lyt.addWidget(chain_lbl)
        laun_lyt.addStretch()
        layout.addLayout(laun_lyt)
        
        layout.addStretch()

    def refresh_sidebar(self):
        # Clear layout
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        self.sidebar_btns = []
        for i, game in enumerate(self.games):
            name = game.get("name", "") or "無題のゲーム"
            btn = QPushButton(f"{i+1}. {name}")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, idx=i: self.select_profile(idx))
            self.scroll_layout.addWidget(btn)
            self.sidebar_btns.append(btn)
            
        self.highlight_sidebar()

    def highlight_sidebar(self):
        if self.current_selected_index is None:
            self.app_settings_btn.setObjectName("SidebarButtonActive")
            for btn in self.sidebar_btns:
                btn.setObjectName("SidebarButton")
        else:
            self.app_settings_btn.setObjectName("SidebarButton")
            for i, btn in enumerate(self.sidebar_btns):
                if i == self.current_selected_index:
                    btn.setObjectName("SidebarButtonActive")
                else:
                    btn.setObjectName("SidebarButton")
                    
        self.sidebar.setStyleSheet(self.sidebar.styleSheet()) # force re-evaluate

    def show_app_settings(self):
        self.sync_current_profile_input()
        self.current_selected_index = None
        self.highlight_sidebar()
        self.stacked.setCurrentWidget(self.app_settings_card)
        self.content_title.setText("アプリ全体設定")
        self.del_btn.setEnabled(False)

    def select_profile(self, index):
        self.sync_current_profile_input()
        self.current_selected_index = index
        self.highlight_sidebar()
        game = self.games[index]
        self.content_title.setText(f"プロファイル: {game.get('name') or '新規プロファイル'}")
        
        self.step_label.setText(f"No. {index + 1}")
        # Stop signals to avoid triggering edit
        self.prof_name_entry.blockSignals(True)
        self.prof_proc_entry.blockSignals(True)
        self.prof_path_entry.blockSignals(True)
        
        self.prof_name_entry.setText(game.get("name", ""))
        self.prof_proc_entry.setText(game.get("process_name", ""))
        self.prof_path_entry.setText(game.get("path", ""))
        self.preset_combo.setCurrentIndex(0)
        
        self.prof_name_entry.blockSignals(False)
        self.prof_proc_entry.blockSignals(False)
        self.prof_path_entry.blockSignals(False)
        
        self.stacked.setCurrentWidget(self.profile_card)
        self.del_btn.setEnabled(True)

    def sync_current_profile_input(self):
        if self.current_selected_index is not None and self.current_selected_index < len(self.games):
            game = self.games[self.current_selected_index]
            game["name"] = self.prof_name_entry.text()
            game["process_name"] = self.prof_proc_entry.text()
            game["path"] = self.prof_path_entry.text()

    def on_profile_edit(self):
        if self.current_selected_index is not None:
            name = self.prof_name_entry.text()
            self.games[self.current_selected_index]["name"] = name
            disp_name = name or "無題のゲーム"
            self.content_title.setText(f"プロファイル: {disp_name}")
            if self.current_selected_index < len(self.sidebar_btns):
                self.sidebar_btns[self.current_selected_index].setText(f"{self.current_selected_index+1}. {disp_name}")

    def on_preset_selected(self, text):
        if text != "プリセット...":
            self.prof_name_entry.setText(text)
            self.preset_combo.setCurrentIndex(0)

    def add_profile(self):
        self.sync_current_profile_input()
        self.games.append({"name": "新規プロファイル", "process_name": "", "path": ""})
        self.refresh_sidebar()
        self.select_profile(len(self.games) - 1)

    def delete_profile(self):
        if self.current_selected_index is not None:
            del self.games[self.current_selected_index]
            self.refresh_sidebar()
            self.show_app_settings()

    def move_up(self):
        idx = self.current_selected_index
        if idx is not None and idx > 0:
            self.sync_current_profile_input()
            self.games[idx-1], self.games[idx] = self.games[idx], self.games[idx-1]
            self.refresh_sidebar()
            self.select_profile(idx - 1)

    def move_down(self):
        idx = self.current_selected_index
        if idx is not None and idx < len(self.games) - 1:
            self.sync_current_profile_input()
            self.games[idx+1], self.games[idx] = self.games[idx], self.games[idx+1]
            self.refresh_sidebar()
            self.select_profile(idx + 1)

    def browse_file(self):
        filename, _ = QFileDialog.getOpenFileName(self, "実行ファイルを選択", "", "Executable files (*.exe);;All files (*.*)")
        if filename:
            filename = filename.replace("/", "\\")
            self.prof_path_entry.setText(filename)
            basename = os.path.basename(filename)
            self.prof_proc_entry.setText(basename)
            if not self.prof_name_entry.text() or self.prof_name_entry.text() == "新規プロファイル":
                self.prof_name_entry.setText(os.path.splitext(basename)[0])

    def auto_detect(self):
        current_name = self.prof_name_entry.text().strip()
        if not current_name or current_name == "新規プロファイル" or current_name == "無題のゲーム":
            QMessageBox.warning(self, "エラー", "ゲーム表示名を入力するか、プリセットから選んでから「自動検出」を押してください。")
            return
            
        target_keywords = []
        target_exe = ""
        
        if "スターレイル" in current_name or "star rail" in current_name.lower():
            target_keywords = ["Star Rail", "スターレイル", "崩壊：スターレイル"]
            target_exe = "StarRail.exe"
        elif "原神" in current_name or "genshin" in current_name.lower():
            target_keywords = ["Genshin", "原神"]
            target_exe = "GenshinImpact.exe"
        elif "鳴潮" in current_name or "wuthering" in current_name.lower() or "wuwa" in current_name.lower():
            target_keywords = ["Wuthering", "鳴潮", "Wuthering Waves"]
            target_exe = "Wuthering Waves.exe"
        else:
            target_keywords = [current_name]
            target_exe = current_name + ".exe"

        found_path = None
        
        # Searching routines identical to old version (omitted deeply nested loops for performance / safety)
        common_static_paths = [
            rf"C:\Program Files\{target_exe.replace('.exe', '')}\Games\{target_exe}",
            rf"C:\Program Files\HoYoPlay\games\{target_exe.replace('.exe', '')}\Games\{target_exe}",
            rf"D:\Program Files\{target_exe.replace('.exe', '')}\Games\{target_exe}",
            rf"D:\Program Files\HoYoPlay\games\{target_exe.replace('.exe', '')}\Games\{target_exe}",
            rf"D:\{target_exe.replace('.exe', '')} Games\{target_exe}",
            rf"D:\HoYoPlay\games\{target_exe.replace('.exe', '')}\Games\{target_exe}",
            rf"C:\Program Files\Genshin Impact\Genshin Impact game\GenshinImpact.exe",
            rf"D:\Genshin Impact\Genshin Impact game\GenshinImpact.exe",
            rf"C:\Program Files\Wuthering Waves\Wuthering Waves Game\Wuthering Waves.exe",
            rf"D:\Wuthering Waves\Wuthering Waves Game\Wuthering Waves.exe",
        ]
        
        if "StarRail.exe" in target_exe:
            common_static_paths.extend([
                r"C:\Program Files\Star Rail\Games\StarRail.exe",
                r"D:\Star Rail\Games\StarRail.exe",
                r"C:\Star Rail\Games\StarRail.exe",
                r"D:\Star Rail Games\StarRail.exe",
                r"C:\Star Rail Games\StarRail.exe",
                r"D:\HoYoPlay\games\Star Rail game\Games\StarRail.exe",
                r"C:\Program Files\HoYoPlay\games\Star Rail game\Games\StarRail.exe"
            ])
            
        for static_path in common_static_paths:
            if os.path.exists(static_path):
                found_path = static_path
                break
                
        if not found_path:
            QMessageBox.information(self, "検出失敗", f"「{current_name}」が見つかりませんでした。手動でご選択ください。")
            return
            
        self.prof_path_entry.setText(found_path.replace("/", "\\"))
        self.prof_proc_entry.setText(os.path.basename(found_path))
        QMessageBox.information(self, "検出成功", f"「{current_name}」が見つかりました！")

    def save_and_close(self):
        self.sync_current_profile_input()
        for game in self.games:
            if not game.get("name") or not game.get("process_name") or not game.get("path"):
                QMessageBox.warning(self, "入力エラー", "未入力の項目があるプロファイルが存在します。")
                return
        if self.save_config():
            if self.on_close_callback:
                self.on_close_callback()
            self.hide()

    def action_start_routine(self):
        if self.monitor and self.games:
            self.monitor.start_specific_game(0, chain_launch=True)
            self.hide()
        elif not self.games:
            QMessageBox.warning(self, "エラー", "ゲームが登録されていません。")

    def action_reset_all(self):
        if not self.games: return
        ret = QMessageBox.question(self, "確認", "すべてのゲームプロファイルを削除しますか？", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if ret == QMessageBox.StandardButton.Yes:
            self.games = []
            self.refresh_sidebar()
            self.show_app_settings()
            self.save_config()

    def launch_current(self):
        if self.current_selected_index is not None and self.monitor:
            path = self.prof_path_entry.text()
            if not path or not os.path.exists(path):
                QMessageBox.critical(self, "エラー", "パスが正しくありません。")
                return
            chain = self.chain_toggle.isChecked()
            success, msg = self.monitor.start_specific_game(self.current_selected_index, chain_launch=chain)
            if success:
                self.hide()
            else:
                QMessageBox.critical(self, "失敗", msg)

    def closeEvent(self, event):
        # We override close event to just hide, unless quit_app is specifically requested
        # Depending on user needs, since they click 'X'
        if self.on_close_callback:
            self.on_close_callback()
        event.ignore()
        self.hide()

# --- Wrapper Interface for Compatibility ---
class GameSetupApp(QObject):
    sig_show = pyqtSignal()
    sig_quit = pyqtSignal()

    def __init__(self, config_path, on_close_callback=None, monitor=None):
        super().__init__()
        self.app = QApplication.instance()
        if not self.app:
            self.app = QApplication(sys.argv)
            self.app.setStyleSheet(MODERN_QSS)
            # Make tooltips modern
            
        self.window = ModernWindow(config_path, on_close_callback, monitor)
        self.sig_show.connect(self.show_window)
        self.sig_quit.connect(self.quit_app)
        
    def safe_show(self):
        self.sig_show.emit()
        
    def safe_quit(self):
        self.sig_quit.emit()
        
    def mainloop(self):
        # PyQt6 needs exec()
        if not QApplication.instance().startingUp():
            sys.exit(self.app.exec())

    def withdraw(self):
        self.window.hide()

    def show_window(self):
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()

    def quit_app(self):
        self.window.on_close_callback = None # Prevent re-trigger
        self.app.quit()

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    app = GameSetupApp(os.path.join(base_dir, "config.json"), None)
    app.show_window()
    app.mainloop()
