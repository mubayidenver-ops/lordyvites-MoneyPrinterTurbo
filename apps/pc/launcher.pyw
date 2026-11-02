"""A self-contained Windows host. All writable data lives outside the installation."""
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import time
import tkinter as tk
from tkinter import messagebox, ttk
import urllib.request
import webbrowser

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
DATA = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "Lordyvites" / "MoneyPrinterTurbo"
DATA.mkdir(parents=True, exist_ok=True)
os.environ["MPT_HOME"] = str(DATA)
os.environ["PYTHONUTF8"] = "1"
os.environ["PYTHONPATH"] = str(ROOT)
from app.config import config


def local_addresses():
    addresses = set()
    try:
        for result in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            address = result[4][0]
            if not address.startswith("127."):
                addresses.add(address)
    except OSError:
        pass
    return sorted(addresses)


class Host:
    def __init__(self):
        self.process = None
        self.log = None
        self.code = ""
        self.root = tk.Tk()
        self.root.title("Lordyvites Money Printer Turbo")
        self.root.geometry("640x700")
        self.root.minsize(580, 640)
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#142019")
        style.configure("TLabel", background="#142019", foreground="#edf4e7", font=("Segoe UI", 10))
        style.configure("Title.TLabel", font=("Segoe UI", 22, "bold"))
        style.configure("TButton", padding=9, font=("Segoe UI", 10))
        frame = ttk.Frame(self.root, padding=28)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="LORDYVITES", style="Title.TLabel").pack(anchor="w")
        ttk.Label(frame, text="Money Printer Turbo · Windows host").pack(anchor="w", pady=(0, 24))
        ttk.Label(frame, text="1. Set up your providers on this computer").pack(anchor="w")
        self.openai = self.field(frame, "OpenAI API key", config.app.get("openai_api_key", ""), secret=True)
        self.model = self.field(frame, "OpenAI model (blank uses the engine default)", config.app.get("openai_model_name", ""))
        ttk.Label(frame, text="Stock-video provider").pack(anchor="w", pady=(8, 3))
        self.source = tk.StringVar(value=config.app.get("desktop_video_source", "pexels"))
        ttk.Combobox(frame, textvariable=self.source, values=["pexels", "pixabay"], state="readonly").pack(fill="x")
        provider_keys = config.app.get(f"{self.source.get()}_api_keys", [])
        self.stock = self.field(frame, "Stock-video API key", provider_keys[0] if provider_keys else "", secret=True)
        ttk.Label(frame, text="Keys stay in your Windows account. Internet and provider access are required.", wraplength=550).pack(anchor="w", pady=8)
        self.start_button = ttk.Button(frame, text="Save settings & start studio", command=self.start)
        self.start_button.pack(fill="x", pady=(14, 10))
        self.status = tk.StringVar(value="Ready to start")
        ttk.Label(frame, textvariable=self.status, wraplength=550).pack(anchor="w", pady=6)
        self.open_button = ttk.Button(frame, text="Open video studio", command=self.open_studio, state="disabled")
        self.open_button.pack(fill="x", pady=6)
        ttk.Label(frame, text="2. Connect your Android companion", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(20, 8))
        self.connection = tk.StringVar(value="Start the studio to see your PC address and pairing code.")
        ttk.Label(frame, textvariable=self.connection, wraplength=550).pack(anchor="w")
        ttk.Label(frame, text="Keep this window open while using your phone. Use trusted Wi-Fi only.\nIf Windows asks, allow network access on Private networks only.", wraplength=550).pack(anchor="w", pady=12)
        row = ttk.Frame(frame)
        row.pack(fill="x", pady=8)
        ttk.Button(row, text="Open videos & logs", command=lambda: os.startfile(DATA)).pack(side="left")
        ttk.Button(row, text="Stop studio", command=self.stop).pack(side="right")
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.mainloop()

    def field(self, frame, label, value, secret=False):
        ttk.Label(frame, text=label).pack(anchor="w", pady=(10, 3))
        variable = tk.StringVar(value=value)
        ttk.Entry(frame, textvariable=variable, show="*" if secret else "").pack(fill="x")
        return variable

    def start(self):
        if self.process and self.process.poll() is None:
            if not messagebox.askyesno("Restart studio?", "Restarting stops any video currently being generated. Continue?"):
                return
            self.stop()
        # Fail early rather than opening an unrelated service on the same port.
        with socket.socket() as probe:
            try:
                probe.bind(("0.0.0.0", 8765))
            except OSError:
                messagebox.showerror("Studio already running", "Port 8765 is busy. Close the other studio window or application, then try again.")
                return
        if not self.stock.get().strip():
            messagebox.showerror("Stock-video key needed", "Enter a Pexels or Pixabay API key to find video clips.")
            return
        config.app["llm_provider"] = "openai"
        config.app["openai_api_key"] = self.openai.get().strip()
        config.app["openai_model_name"] = self.model.get().strip()
        config.app["desktop_video_source"] = self.source.get()
        config.app[f"{self.source.get()}_api_keys"] = [self.stock.get().strip()]
        config.app["api_key"] = ""
        config.app["endpoint"] = ""
        config.save_config()
        self.code = "".join(str(secrets.randbelow(10)) for _ in range(12))
        env = os.environ.copy()
        env["LORDYVITES_PAIR_CODE"] = self.code
        python = Path(sys.executable).with_name("python.exe")
        self.log = (DATA / "studio.log").open("a", encoding="utf-8")
        try:
            self.process = subprocess.Popen([str(python), "-m", "apps.pc.server"], cwd=ROOT, env=env,
                                            stdout=self.log, stderr=self.log,
                                            creationflags=subprocess.CREATE_NO_WINDOW)
        except OSError as error:
            self.log.close()
            self.log = None
            messagebox.showerror("Could not start", str(error))
            return
        self.status.set("Starting video engine. The first launch can take a minute…")
        self.start_button.configure(state="disabled")
        self.deadline = time.monotonic() + 180
        self.root.after(1000, self.check_ready)

    def check_ready(self):
        if not self.process:
            return
        if self.process.poll() is not None:
            self.status.set("The engine could not start. Open studio.log in the data folder for details.")
            self.start_button.configure(state="normal")
            return
        ready = False
        try:
            with urllib.request.urlopen("http://127.0.0.1:8765/health", timeout=.5) as response:
                ready = json.load(response).get("application") == "lordyvites"
        except (OSError, ValueError):
            pass
        if ready:
            self.status.set("Studio running · Closing this app stops video generation.")
            addresses = local_addresses()
            links = "\n".join(f"PC address: http://{address}:8765" for address in addresses) or "No Wi-Fi address found. Connect your PC to Wi-Fi."
            self.connection.set(links + "\nPairing code: " + " ".join(self.code[i:i+4] for i in range(0, 12, 4)))
            self.open_button.configure(state="normal")
            self.start_button.configure(state="normal")
            self.open_studio()
            self.root.after(3000, self.monitor)
        elif time.monotonic() > self.deadline:
            self.stop()
            self.status.set("Startup timed out. Open studio.log to see the error.")
        else:
            self.root.after(1000, self.check_ready)

    def monitor(self):
        if self.process and self.process.poll() is None:
            self.root.after(3000, self.monitor)
        elif self.process:
            self.stop()
            self.status.set("Video engine stopped unexpectedly. Check studio.log, then restart.")

    def open_studio(self):
        webbrowser.open("http://127.0.0.1:8765/#pair=" + self.code)

    def stop(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)
        self.process = None
        if self.log:
            self.log.close()
            self.log = None
        self.open_button.configure(state="disabled")
        self.start_button.configure(state="normal")
        self.status.set("Studio stopped")
        self.connection.set("Start the studio to create a new pairing code.")

    def close(self):
        if self.process and self.process.poll() is None and not messagebox.askyesno("Close studio?", "Closing stops video generation and disconnects your phone. Continue?"):
            return
        self.stop()
        self.root.destroy()


if __name__ == "__main__":
    try:
        Host()
    except Exception as error:
        messagebox.showerror("Lordyvites could not start", f"{error}\n\nYour data is in {DATA}")
