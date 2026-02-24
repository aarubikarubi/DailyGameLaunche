import json
import time
import psutil
import subprocess
import threading
import os
import ctypes
from enum import Enum

from datetime import datetime

class State(Enum):
    STANDBY = 0
    STAR_RAIL = 1
    GENSHIN = 2
    WUTHERING_WAVES = 3

class GameMonitor:
    def __init__(self, config_path=None):
        if config_path is None:
            self.config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
        else:
            self.config_path = config_path
        self.state = State.STANDBY
        self.waiting_for_launch = False
        self.launch_sleep_remaining = 0
        
        # Config
        self.games = []
        self.launch_interval = 5
        self.kill_targets = []
        
        # Tracking
        self.chain_launch_active = True
        self.last_reset_date = datetime.now().date()
        
        self._running = False
        self._thread = None
        self.auto_exit_after_completion = False
        self.on_completion_callback = None
        self.load_config()

    def load_config(self):
        try:
            if not os.path.exists(self.config_path):
                print(f"Config file not found: {self.config_path}")
                return
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                self.games = config.get("games", [])
                self.launch_interval = config.get("launch_interval", 5)
                self.kill_targets = config.get("kill_targets", [])
                self.auto_exit_after_completion = config.get("auto_exit_after_completion", False)
        except Exception as e:
            print(f"Failed to load config: {e}")

    def save_config(self):
        try:
            config_data = {
                "games": self.games,
                "launch_interval": self.launch_interval,
                "kill_targets": self.kill_targets,
                "auto_exit_after_completion": self.auto_exit_after_completion
            }
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Failed to save config: {e}")

    def is_process_running(self, process_name):
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'].lower() == process_name.lower():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return False
        
    def kill_target_processes(self):
        # Create a list of actual process names to kill (e.g., extracting "hoyoplay.exe" from "HoYoPlay (hoyoplay.exe)")
        actual_targets = []
        for target in self.kill_targets:
            if not target or target == "なし":
                continue
            # Try to extract from parentheses
            if "(" in target and ")" in target:
                proc_name = target.split("(")[-1].split(")")[0]
                actual_targets.append(proc_name.strip().lower())
            else:
                actual_targets.append(target.strip().lower())

        for proc in psutil.process_iter(['name']):
            try:
                name = proc.info.get('name')
                if name and name.lower() in actual_targets:
                    print(f"Auto-killing process: {name}")
                    proc.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

    def launch_game(self, game_index):
        if game_index < len(self.games):
            path = self.games[game_index].get("path")
            try:
                if not path or not os.path.exists(path):
                    msg = f"Failed to launch {self.games[game_index]['name']}: Invalid path or file not found."
                    print(msg)
                    return False, msg
                # Extract the parent directory to use as current working directory (cwd)
                cwd = os.path.dirname(path)
                
                # Use ShellExecuteW to correctly launch games that require Admin privileges (WinError 740)
                # This handles UAC prompt and allows specifying the working directory (cwd).
                # hwnd=0, op="open", file=path, params=None, dir=cwd, nShow=1
                ret = ctypes.windll.shell32.ShellExecuteW(0, "open", path, None, cwd, 1)
                
                if ret > 32:
                    print(f"Launched: {self.games[game_index]['name']} (cwd: {cwd})")
                    return True, ""
                else:
                    msg = f"ShellExecute failed with error code: {ret}"
                    print(msg)
                    return False, msg
            except Exception as e:
                msg = f"Failed to launch {self.games[game_index]['name']}: {e}"
                print(msg)
                return False, msg
        return False, "Invalid game index."

    def get_status_text(self):
        if self.state == State.STANDBY:
            if not self.games:
                return "待機中 (ゲームが登録されていません)"
            return f"待機中 ({self.games[0]['name']}の起動待ち)"
        
        # 動的な状態テキストの生成（state は 1以降が各ゲームに対応）
        if self.state != State.STANDBY and int(self.state.value) <= len(self.games):
            current_game_index = int(self.state.value) - 1
            current_name = self.games[current_game_index]['name']
            
            if self.launch_sleep_remaining > 0:
                return f"インターバル待機中... ({self.launch_sleep_remaining}秒後)"
            
            if current_game_index + 1 < len(self.games):
                next_name = self.games[current_game_index + 1]['name']
                if self.chain_launch_active:
                    return f"{current_name} プレイ中 (終了後に {next_name} を起動)"
                else:
                    return f"{current_name} プレイ中 (単独起動)"
            else:
                return f"{current_name} プレイ中 (これで最後です)"
                
        return "不明"
        
    def start_specific_game(self, index, chain_launch=True):
        self.chain_launch_active = chain_launch
        if index < len(self.games):
            self.state = State(index + 1)
            self.launch_sleep_remaining = 0
            self.waiting_for_launch = True
            # Launch immediately
            return self.launch_game(index)
        return False, "Invalid game index."

    def reset_state(self):
        self.state = State.STANDBY
        self.waiting_for_launch = False
        self.launch_sleep_remaining = 0
        
    def skip_current(self):
        if self.state == State.STANDBY or len(self.games) == 0:
            return
            
        print("Skipping current game...")
        current_idx = int(self.state.value) - 1
        next_idx = current_idx + 1
        
        self.kill_target_processes()
        
        if next_idx < len(self.games):
            if self.chain_launch_active:
                next_name = self.games[next_idx]["name"]
                print(f"Skipped to {next_name}. Waiting interval...")
                self.launch_sleep_remaining = self.launch_interval
                self.state = State(next_idx + 1)
                self.waiting_for_launch = True
            else:
                print("Skipped single play.")
                self._handle_completion()
        else:
            print("Skipped to end. Daily sequence completed!")
            self._handle_completion()

    def _handle_completion(self):
        self.state = State.STANDBY
        self.waiting_for_launch = False
        print("デイリー完了！待機状態に戻ります。")
        if self.auto_exit_after_completion and self.on_completion_callback:
            print("Auto-exit is enabled. Triggering completion callback.")
            self.on_completion_callback()

    def _monitor_loop(self):
        while self._running:
            try:
                # 5 AM reset check
                now = datetime.now()
                if now.hour == 5 and now.date() > self.last_reset_date:
                    print("5 AM reached. Resetting daily state.")
                    self.reset_state()
                    self.last_reset_date = now.date()

                # Interval Wait Routine
                if self.launch_sleep_remaining > 0:
                    self.launch_sleep_remaining -= 1
                    if self.launch_sleep_remaining <= 0:
                        # 待機明けたら起動
                        current_idx = int(self.state.value) - 1
                        if current_idx < len(self.games):
                            self.launch_game(current_idx)
                            # ここで改めて起動待機中フラグを有効にする（実体が上がるまで待つ）
                            self.waiting_for_launch = True
                    time.sleep(1)
                    continue
                    
                # ゲームが未登録の場合は待機のみ
                if not self.games:
                    time.sleep(3)
                    continue

                if self.state == State.STANDBY:
                    # 待機中：最初のゲームが起動したらState 1へ
                    first_proc = self.games[0]["process_name"]
                    if self.is_process_running(first_proc):
                        self.state = State(1)
                        self.waiting_for_launch = False
                        self.kill_target_processes()
                        print(f"State changed to: 1 ({first_proc})")
                else:
                    # ゲームプレイ中の処理（stateは1以上）
                    current_idx = int(self.state.value) - 1
                    
                    if current_idx >= len(self.games):
                        self.reset_state()
                        continue
                        
                    current_proc = self.games[current_idx]["process_name"]

                    if self.waiting_for_launch:
                        # 起動待機中：プロセスが立ち上がるのを待つ
                        if self.is_process_running(current_proc):
                            self.waiting_for_launch = False
                            print(f"{current_proc} is running.")
                    else:
                        # 監視中：プロセスが終了したら次のゲームへ
                        if not self.is_process_running(current_proc):
                            print(f"{current_proc} has exited.")
                            self.kill_target_processes()
                            
                            next_idx = current_idx + 1
                            if self.chain_launch_active and next_idx < len(self.games):
                                # 次のゲームがある場合
                                next_name = self.games[next_idx]["name"]
                                print(f"Preparing to launch {next_name} in {self.launch_interval}s...")
                                self.state = State(next_idx + 1)
                                self.launch_sleep_remaining = self.launch_interval
                            else:
                                # これが最後のゲームだった場合、または連鎖OFF
                                print("Sequence completed or single play finished!")
                                self._handle_completion()

            except Exception as e:
                print(f"Monitor error: {e}")
            
            time.sleep(3)  # 3秒間隔でプロセスをチェック

    def start(self):
        if not self._running:
            self._running = True
            self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
