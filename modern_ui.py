from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QColor, QFont, QKeySequence, QPainter, QPen, QBrush
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QFrame, QLabel, QPushButton, QLineEdit, QComboBox,
    QDoubleSpinBox, QSlider, QCheckBox, QHBoxLayout, QVBoxLayout, QGridLayout,
    QSizePolicy, QGraphicsDropShadowEffect, QMessageBox
)

STYLE = """
QWidget#root { background: transparent; color: #F5F8FA; font-family: 'Segoe UI'; font-size: 12px; }
QFrame#surface { background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #202D35, stop:.48 #17232B, stop:1 #111C23); border: 1px solid #35505A; border-radius: 18px; }
QFrame#titleBar { background: rgba(10,18,24,225); border: none; border-top-left-radius: 18px; border-top-right-radius: 18px; }
QFrame#statusCard, QFrame#shortcutCard, QFrame#preferencesCard { background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 rgba(28,43,51,245), stop:1 rgba(17,29,36,245)); border: 1.5px solid #37C7D5; border-radius: 17px; }
QFrame#shortcutCard { border-color: #43A9E9; }
QFrame#preferencesCard { background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 rgba(43,59,67,245), stop:.27 rgba(29,45,53,245), stop:.29 rgba(23,38,46,245), stop:1 rgba(18,31,39,245)); border-color: #63DCE0; }
QLabel#eyebrow { color: #73E7DF; font-size: 12px; font-weight: 700; letter-spacing: 1px; }
QLabel#title { color: #F7FAFC; font-size: 26px; font-weight: 700; }
QLabel#subtitle { color: #B2C1C8; font-size: 12px; }
QLabel#statusPill { background: rgba(30,48,57,235); border: 1px solid #48727D; border-radius: 16px; padding: 9px 14px; color: #7DE9DD; font-weight: 700; font-size: 12px; }
QPushButton { border: 1px solid rgba(101,226,233,150); border-radius: 10px; padding: 9px 14px; color: #D6FBFA; background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #25434E, stop:1 #1A3039); font-weight: 600; font-size: 12px; }
QPushButton:hover { border: 1px solid #A7FFFF; background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #32636F, stop:1 #21434C); }
QPushButton#primaryButton { color: #F4FFFF; border: 1px solid #6DF5F1; background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #247E8C, stop:1 #31599A); }
QPushButton#primaryButton:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #31A5AE, stop:1 #476DC5); }
QPushButton#editButton { min-width: 40px; max-width: 40px; min-height: 38px; padding: 0; color: #8BFBF4; font-size: 18px; border-radius: 11px; }
QPushButton#startupButton { text-align: left; border: 1px solid #7DFFC0; border-radius: 10px; background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #CEFFE0, stop:1 #A6F4C5); color: #145638; padding: 12px 14px; font-size: 12px; font-weight: 700; }
QPushButton#startupButton[enabled="false"] { border-color: #50656D; background: #223139; color: #B2C1C8; }
QLineEdit, QComboBox, QDoubleSpinBox { color: #F2F7F9; background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #26363E, stop:1 #202E35); border: 1px solid #526A73; border-radius: 9px; padding: 9px 11px; selection-background-color: #2FAAB5; min-height: 22px; font-size: 12px; }
QLineEdit:focus, QComboBox:focus, QDoubleSpinBox:focus { border: 1px solid #70F1EB; }
QComboBox::drop-down { border: none; width: 30px; }
QComboBox::down-arrow { image: none; width: 0px; height: 0px; border: none; }
QComboBox QAbstractItemView { background: #1A2931; color: #F2F7F9; selection-background-color: #276B78; border: 1px solid #4ABEC8; outline: 0; }
QSlider::groove:horizontal { height: 8px; border-radius: 4px; background: #293B43; border: 1px solid #405861; }
QSlider::sub-page:horizontal { border-radius: 4px; background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #27AABC, stop:1 #62F0E4); }
QSlider::handle:horizontal { background: #E8FFFF; border: 2px solid #4FE0E0; width: 18px; height: 18px; margin: -7px 0; border-radius: 10px; }
QCheckBox { spacing: 9px; color: #E5EEF0; font-size: 12px; font-weight: 600; }
QCheckBox::indicator { width: 17px; height: 17px; border-radius: 5px; border: 1px solid #4C7079; background: #23343C; }
QCheckBox::indicator:checked { background: #6BE8B2; border-color: #A8FFD1; }
"""

class MicBadge(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent); self.setFixedSize(56, 56)
    def paintEvent(self, _event):
        p=QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing); p.scale(self.width()/56.0,self.height()/56.0)
        p.setPen(QPen(QColor("#68F3EB"),2)); p.setBrush(QBrush(QColor("#203740"))); p.drawEllipse(3,3,50,50)
        p.setPen(QPen(QColor("#8BFFF5"),3,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap,Qt.PenJoinStyle.RoundJoin))
        p.drawRoundedRect(22,12,12,23,6,6); p.drawArc(16,17,24,26,190*16,160*16); p.drawLine(28,40,28,46); p.drawLine(22,47,34,47)

class ArrowComboBox(QComboBox):
    def paintEvent(self,event):
        super().paintEvent(event)
        p=QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing); p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor("#70E9E5"))
        x=self.width()-16; y=self.height()/2
        from PySide6.QtGui import QPolygonF
        from PySide6.QtCore import QPointF
        p.drawPolygon(QPolygonF([QPointF(x-5,y-2),QPointF(x+5,y-2),QPointF(x,y+4)]))

class ShortcutEdit(QLineEdit):
    def __init__(self, text):
        super().__init__(text); self.capture=False; self.setReadOnly(True); self.setAlignment(Qt.AlignmentFlag.AlignCenter)
    def keyPressEvent(self,event):
        if not self.capture: return super().keyPressEvent(event)
        mods=[]; m=event.modifiers()
        if m & Qt.KeyboardModifier.ControlModifier: mods.append("ctrl")
        if m & Qt.KeyboardModifier.AltModifier: mods.append("alt")
        if m & Qt.KeyboardModifier.ShiftModifier: mods.append("shift")
        key=event.key(); names={Qt.Key.Key_Return:"enter",Qt.Key.Key_Enter:"enter",Qt.Key.Key_Escape:"esc",Qt.Key.Key_Space:"space",Qt.Key.Key_Backspace:"backspace",Qt.Key.Key_Tab:"tab",Qt.Key.Key_Delete:"delete"}
        if key not in (Qt.Key.Key_Control,Qt.Key.Key_Alt,Qt.Key.Key_Shift,Qt.Key.Key_Meta):
            name=names.get(key,event.text().lower() or QKeySequence(key).toString().lower())
            if name and name not in mods: mods.append(name)
        if mods: self.setText("+".join(mods))
        event.accept()

class WindowControlButton(QPushButton):
    def __init__(self, kind, callback, parent=None):
        super().__init__(parent)
        self.kind=kind
        self.clicked.connect(callback)
        self.setFixedSize(38,30)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    def paintEvent(self,event):
        p=QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.underMouse():
            fill="#A92E3A" if self.kind=="close" else "#344C56"
            p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(fill)); p.drawRoundedRect(1,1,self.width()-2,self.height()-2,5,5)
        color=QColor("#EDF7F8" if self.underMouse() else "#C6D5DA")
        p.setPen(QPen(color,1.7,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap,Qt.PenJoinStyle.RoundJoin))
        cx,cy=self.width()//2,self.height()//2
        if self.kind=="minimize": p.drawLine(cx-6,cy+3,cx+6,cy+3)
        elif self.kind=="maximize": p.drawRect(cx-6,cy-6,12,12)
        else:
            p.drawLine(cx-5,cy-5,cx+5,cy+5); p.drawLine(cx+5,cy-5,cx-5,cy+5)

class ControlCenter(QMainWindow):
    def __init__(self, owner):
        super().__init__(); self.owner=owner; self._drag_offset=None
        self.setWindowTitle("Bangla Voice Tray · Control Center")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(1020,780); self.setMinimumSize(900,700); self.setStyleSheet(STYLE)
        self.setWindowOpacity(float(owner.config.get("window_opacity",.98)))
        root=QWidget(); root.setObjectName("root"); outer=QVBoxLayout(root); outer.setContentsMargins(5,5,5,5)
        surface=QFrame(); surface.setObjectName("surface"); shadow=QGraphicsDropShadowEffect(surface); shadow.setBlurRadius(34); shadow.setOffset(0,8); shadow.setColor(QColor(0,0,0,155)); surface.setGraphicsEffect(shadow); outer.addWidget(surface)
        v=QVBoxLayout(surface); v.setContentsMargins(20,9,20,14); v.setSpacing(11)
        v.addWidget(self._title_bar())
        v.addWidget(self._header())
        v.addWidget(self._status_card())
        v.addWidget(self._shortcut_card())
        v.addWidget(self._preferences_card(),1)
        v.addWidget(self._footer())
        self.setCentralWidget(root)
        self.timer=QTimer(self); self.timer.timeout.connect(self.refresh); self.timer.start(350); self.refresh()

    def _shadow(self, widget, color="#3DE2E3", blur=26, y=3):
        effect=QGraphicsDropShadowEffect(widget); effect.setBlurRadius(blur); effect.setOffset(0,y); effect.setColor(QColor(color)); widget.setGraphicsEffect(effect)
    def _card(self,name,glow="#39D5DC"):
        frame=QFrame(); frame.setObjectName(name); self._shadow(frame,glow,24,2); return frame
    def _title_bar(self):
        bar=QFrame(); bar.setObjectName("titleBar"); bar.setFixedHeight(36); h=QHBoxLayout(bar); h.setContentsMargins(9,0,6,0); h.setSpacing(5)
        icon=MicBadge(); icon.setFixedSize(22,22); h.addWidget(icon)
        name=QLabel("Bangla Voice Tray  ·  Control Center"); name.setStyleSheet("color:#D7E2E7;font-size:11px;"); h.addWidget(name); h.addStretch(1)
        for kind,fn in (("minimize",self.showMinimized),("maximize",self._toggle_maximize),("close",self.close)):
            h.addWidget(WindowControlButton(kind,fn,bar))
        bar.mousePressEvent=self._title_press; bar.mouseMoveEvent=self._title_move; return bar
    def _title_press(self,event):
        if event.button()==Qt.MouseButton.LeftButton: self._drag_offset=event.globalPosition().toPoint()-self.frameGeometry().topLeft()
    def _title_move(self,event):
        if self._drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton: self.move(event.globalPosition().toPoint()-self._drag_offset)
    def _toggle_maximize(self): self.showNormal() if self.isMaximized() else self.showMaximized()
    def _header(self):
        w=QWidget(); h=QHBoxLayout(w); h.setContentsMargins(1,0,1,2); h.setSpacing(12)
        h.addWidget(MicBadge()); titles=QVBoxLayout(); titles.setSpacing(1)
        title=QLabel("Bangla Voice Tray"); title.setObjectName("title")
        sub=QLabel("VOICE CONTROL CENTER  ·  বাংলা ভয়েস টাইপিং"); sub.setObjectName("subtitle")
        titles.addWidget(title); titles.addWidget(sub); h.addLayout(titles); h.addStretch(1)
        self.ready=QLabel("●  READY"); self.ready.setObjectName("statusPill"); h.addWidget(self.ready,0,Qt.AlignmentFlag.AlignTop)
        return w
    def _status_card(self):
        card=self._card("statusCard","#39D9DF"); h=QHBoxLayout(card); h.setContentsMargins(17,12,17,12); h.setSpacing(14)
        self.status_pill=QLabel("●  MICROPHONE OFF  ·  READY"); self.status_pill.setObjectName("statusPill"); h.addWidget(self.status_pill,0,Qt.AlignmentFlag.AlignVCenter)
        self.status_detail=QLabel(self.owner.last_status); self.status_detail.setStyleSheet("color:#B3C1C7;font-size:11px;"); h.addWidget(self.status_detail,1)
        self.mic_button=QPushButton("🎙  START LISTENING"); self.mic_button.setObjectName("primaryButton"); self.mic_button.clicked.connect(self.owner.toggle_listening); h.addWidget(self.mic_button)
        return card
    def _shortcut_card(self):
        card=self._card("shortcutCard","#398FE8"); v=QVBoxLayout(card); v.setContentsMargins(17,12,17,10); v.setSpacing(5)
        eyebrow=QLabel("SHORTCUT"); eyebrow.setObjectName("eyebrow"); v.addWidget(eyebrow)
        title=QLabel("মাইক্রোফোন চালু / বন্ধ করার key বেছে নিন"); title.setStyleSheet("font-size:15px;font-weight:700;color:#F6F8FA;"); v.addWidget(title)
        row=QHBoxLayout(); row.setSpacing(9)
        self.hotkey=ShortcutEdit(self.owner.config.get("toggle_hotkey","ctrl+shift+b")); self.hotkey.setStyleSheet("font-size:15px;font-weight:700;color:#F5F8FA;"); row.addWidget(self.hotkey,1)
        self.edit_button=QPushButton("✎"); self.edit_button.setObjectName("editButton"); self.edit_button.setToolTip("Shortcut পরিবর্তন করুন"); self.edit_button.clicked.connect(self._edit_hotkey); row.addWidget(self.edit_button)
        v.addLayout(row)
        hint=QLabel("একটি key বা combination চাপুন · যেমন F8, Ctrl + B"); hint.setStyleSheet("color:#A9BBC2;font-size:10px;"); v.addWidget(hint)
        return card
    def _edit_hotkey(self):
        self.hotkey.capture=True; self.hotkey.setReadOnly(False); self.hotkey.setText("Press a key combination…"); self.hotkey.setFocus(); self.hotkey.selectAll()
    def _preferences_card(self):
        card=self._card("preferencesCard","#40C8D4"); v=QVBoxLayout(card); v.setContentsMargins(17,12,17,12); v.setSpacing(8)
        eyebrow=QLabel("PREFERENCES BOX"); eyebrow.setObjectName("eyebrow"); v.addWidget(eyebrow)
        grid=QGridLayout(); grid.setContentsMargins(0,0,0,0); grid.setHorizontalSpacing(16); grid.setVerticalSpacing(8); grid.setColumnStretch(0,1)
        def field_label(text):
            l=QLabel(text); l.setStyleSheet("color:#D1DCE0;font-size:13px;"); return l
        self.language=ArrowComboBox(); self.language.addItem("বাংলা (বাংলাদেশ)","bn-BD"); self.language.addItem("English (US)","en-US"); self.language.addItem("हिन्दी (भारत)","hi-IN")
        idx=self.language.findData(self.owner.config.get("language","bn-BD")); self.language.setCurrentIndex(max(0,idx)); self.language.setFixedWidth(200)
        grid.addWidget(field_label("ডিকটেশনের ভাষা"),0,0); grid.addWidget(self.language,0,1,Qt.AlignmentFlag.AlignRight)
        self.device=ArrowComboBox()
        self.devices={"System default":None}; self.device.addItem("System default",None)
        for i,name in enumerate(getattr(self.owner,"microphone_names",[])):
            label=f"{i+1}. {name}"; self.devices[label]=i; self.device.addItem(label,i)
        configured=self.owner.config.get("microphone_device_index"); self.device.setCurrentIndex(max(0,self.device.findData(configured))); self.device.setFixedWidth(200)
        grid.addWidget(field_label("Microphone input"),1,0); grid.addWidget(self.device,1,1,Qt.AlignmentFlag.AlignRight)
        self.delay=QDoubleSpinBox(); self.delay.setRange(0,2); self.delay.setSingleStep(.05); self.delay.setDecimals(2); self.delay.setValue(float(self.owner.config.get("paste_delay",.15))); self.delay.setSuffix(" s"); self.delay.setFixedWidth(120)
        grid.addWidget(field_label("Paste delay (সেকেন্ড)"),2,0); grid.addWidget(self.delay,2,1,Qt.AlignmentFlag.AlignRight)
        v.addLayout(grid)
        self.startup=QPushButton(); self.startup.setObjectName("startupButton"); self.startup.setCheckable(True); self.startup.setChecked(bool(self.owner.config.get("start_with_windows",True))); self._startup_text(); self.startup.toggled.connect(self._startup_text); v.addWidget(self.startup)
        opacity_row=QHBoxLayout(); self.opacity_label=QLabel(); self.opacity_label.setStyleSheet("color:#CFD9DD;font-size:10px;font-weight:600;"); opacity_row.addWidget(self.opacity_label); opacity_row.addStretch(1); self.opaque=QLabel("Opaque"); self.opaque.setStyleSheet("color:#AAB8BE;font-size:10px;"); opacity_row.addWidget(self.opaque); v.addLayout(opacity_row)
        self.opacity=QSlider(Qt.Orientation.Horizontal); self.opacity.setRange(72,100); self.opacity.setSingleStep(2); self.opacity.setPageStep(4); self.opacity.setValue(round(float(self.owner.config.get("window_opacity",.98))*100)); self.opacity.valueChanged.connect(self._opacity_changed); v.addWidget(self.opacity); self._opacity_changed(self.opacity.value())
        lower=QHBoxLayout(); lower.addStretch(1); self.permission=QPushButton("মাইক্রোফোন permission খুলুন"); self.permission.clicked.connect(self._open_mic_settings); lower.addWidget(self.permission); v.addLayout(lower)
        return card
    def _startup_text(self):
        self.startup.setText("✓  Windows চালু হলে অ্যাপ চালু হবে  ·  চালু" if self.startup.isChecked() else "○  Windows চালু হলে অ্যাপ চালু হবে  ·  বন্ধ")
        self.startup.setProperty("enabled",self.startup.isChecked()); self.startup.style().unpolish(self.startup); self.startup.style().polish(self.startup)
    def _opacity_changed(self,value):
        self.opacity_label.setText(f"Window transparency  ·  {value}%")
        self.setWindowOpacity(value/100.0)
    def _open_mic_settings(self):
        import os
        try: os.startfile("ms-settings:privacy-microphone")
        except Exception as e: QMessageBox.warning(self,"Microphone permission",str(e))
    def _footer(self):
        w=QWidget(); h=QHBoxLayout(w); h.setContentsMargins(2,0,2,0); h.setSpacing(9)
        self.footer_status=QLabel(self.owner.last_status); self.footer_status.setStyleSheet("color:#B5C2C8;font-size:11px;"); h.addWidget(self.footer_status,1)
        close=QPushButton("বন্ধ করুন"); close.clicked.connect(self.close); h.addWidget(close)
        save=QPushButton("✓  শর্টকাট ও সেটিংস সংরক্ষণ"); save.setObjectName("primaryButton"); save.clicked.connect(self._save); h.addWidget(save)
        return w
    def _save(self):
        hotkey=self.hotkey.text().strip().lower()
        if not hotkey or hotkey.startswith("press a key"):
            QMessageBox.warning(self,"Shortcut required","একটি shortcut key বেছে নিন।",self); return
        config={"toggle_hotkey":hotkey,"language":self.language.currentData(),"microphone_device_index":self.device.currentData(),"paste_delay":self.delay.value(),"start_with_windows":self.startup.isChecked(),"window_opacity":self.opacity.value()/100.0}
        ok,error=self.owner.save_gui_settings(config)
        if not ok:
            QMessageBox.warning(self,"Settings not saved",error,self); return
        self.hotkey.setReadOnly(True); self.hotkey.capture=False
        self.owner.last_status="সেটিংস সংরক্ষিত · shortcut: "+hotkey; self.footer_status.setText(self.owner.last_status)
    def refresh(self):
        active=bool(self.owner.active)
        self.status_pill.setText("●  MICROPHONE ON  ·  LISTENING" if active else "●  MICROPHONE OFF  ·  READY")
        self.status_pill.setStyleSheet("background:rgba(30,48,57,235);border:1px solid #48727D;border-radius:16px;padding:9px 14px;font-weight:700;color:"+("#FF7580" if active else "#7DE9DD")+";")
        self.ready.setText("●  LISTENING" if active else "●  READY"); self.ready.setStyleSheet("background:rgba(30,48,57,235);border:1px solid #48727D;border-radius:16px;padding:9px 14px;font-weight:700;color:"+("#FF7580" if active else "#7DE9DD")+";")
        self.mic_button.setText("⏹  STOP LISTENING" if active else "🎙  START LISTENING")
        self.status_detail.setText(self.owner.last_status); self.footer_status.setText(self.owner.last_status)
    def closeEvent(self,event):
        self.timer.stop()
        self.owner.dashboard_window=None
        event.accept()
