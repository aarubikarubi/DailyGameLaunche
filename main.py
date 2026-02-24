import pystray
from PIL import Image, ImageDraw
import threading
from core import GameMonitor, State
import time
import sys
import os
import setup_ui
import keyboard
import update_manager

def create_image():
    # シンプルなアイコン（緑色の四角形）を生成
    image = Image.new('RGB', (64, 64), color=(30, 30, 30))
    d = ImageDraw.Draw(image)
    d.rectangle(
        [(16, 16), (48, 48)],
        fill=(100, 200, 100)
    )
    return image

def update_menu(icon, monitor):
    # メニューを動的に更新するためのプロパティ
    status = monitor.get_status_text()
    if monitor.waiting_for_launch:
        status += " (起動待機中...)"
    
    menu = pystray.Menu(
        pystray.MenuItem("現在の状態: ", lambda: None, enabled=False),
        pystray.MenuItem(lambda text: monitor.get_status_text(), lambda: None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("▶ 日課を開始", lambda: action_start_routine(icon, monitor)),
        pystray.MenuItem("⏭ 次のゲームへ強制スキップ", lambda: action_skip(icon, monitor)),
        pystray.MenuItem("設定画面を開く", lambda: action_settings()),
        pystray.MenuItem("リセット (待機に戻す)", lambda: action_reset(icon, monitor)),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("完全に終了", lambda: action_exit(icon, monitor))
    )
    icon.menu = menu

def action_skip(icon, monitor):
    monitor.skip_current()
    update_icon_menu(icon, monitor)

def action_start_routine(icon, monitor):
    if monitor.games:
        monitor.start_specific_game(0, chain_launch=True)
        update_icon_menu(icon, monitor)

def update_icon_menu(icon, monitor):
    update_menu(icon, monitor)

def action_reset(icon, monitor):
    monitor.reset_state()
    update_icon_menu(icon, monitor)

def action_settings():
    if 'app' in globals() and app:
        app.safe_show()

def action_exit(icon, monitor):
    monitor.stop()
    icon.stop()
    if 'app' in globals() and app:
        app.safe_quit()

def monitor_state_changes(icon, monitor):
    # 状態が変わったときにメニュー表記を更新するバックグラウンドタスク
    last_state = monitor.state
    last_waiting = monitor.waiting_for_launch
    last_games_count = len(monitor.games)
    
    while monitor._running:
        current_count = len(monitor.games)
        if last_state != monitor.state or last_waiting != monitor.waiting_for_launch or last_games_count != current_count:
            last_state = monitor.state
            last_waiting = monitor.waiting_for_launch
            last_games_count = current_count
            update_icon_menu(icon, monitor)
        time.sleep(1)

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_dir, "config.json")
    
    monitor = GameMonitor(config_path=config_path)
    monitor.start()
    
    def on_settings_close():
        monitor.load_config()
        monitor.reset_state()
        if 'icon' in globals():
            update_icon_menu(icon, monitor)
            
    # GUIのインスタンスをメインスレッドで作成
    app = setup_ui.GameSetupApp(config_path, on_close_callback=on_settings_close, monitor=monitor)
    
    # 起動時の自動アップデート確認
    update_manager.check_and_apply_updates(app.window)
    
    # --startup 引数がある場合のみタスクトレイに最小化して起動
    if "--startup" in sys.argv:
        app.withdraw()
        
    icon = pystray.Icon("DailyChainLauncher", create_image(), "日課ツール")
    update_menu(icon, monitor)
    
    # メニュー更新用スレッド
    update_thread = threading.Thread(target=monitor_state_changes, args=(icon, monitor), daemon=True)
    update_thread.start()
    
    # 日課完了時の自動終了コールバックを設定
    monitor.on_completion_callback = lambda: action_exit(icon, monitor)
    
    # タスクトレイアイコンを別スレッドで実行
    icon_thread = threading.Thread(target=icon.run, daemon=True)
    icon_thread.start()
    
    # グローバルホットキーの登録
    try:
        keyboard.add_hotkey('ctrl+shift+s', lambda: action_skip(icon, monitor))
    except Exception as e:
        print(f"Failed to register hotkey: {e}")
    
    # tkinterメインループをメインスレッドで実行
    app.mainloop()
    
    # メインループ終了後、念のためリソースを解放
    monitor.stop()
    if 'icon' in globals():
        icon.stop()
