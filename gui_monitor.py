import tkinter as tk
from tkinter import ttk
import threading
import time
import psutil
import pynvml
import json
import os
import logging
from datetime import datetime
import traceback

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('d:', 'logs', 'gui_monitor.log'), mode='w'),
        logging.StreamHandler()
    ]
)

class Monitor:
    def __init__(self, root):
        print("Initializing Monitor")
        self.root = root
        self.root.title("Video Processing Monitor")
        self.root.geometry("600x400")
        
        # Initialize GPU monitoring
        try:
            pynvml.nvmlInit()
            self.handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        except Exception as e:
            self.handle = None
            logging.warning(f"GPU monitoring initialization error: {str(e)}")
            print(f"GPU initialization error: {str(e)}")
            
        # Create UI elements
        self.create_widgets()
        
        # Initialize metrics
        self.progress = 0
        self.detections = 0
        self.fps = 0
        self.gpu_usage = 0
        self.cpu_usage = 0
        self.memory_usage = 0
        self.last_update = datetime.now()
        
        # Start update thread
        self.update_thread = threading.Thread(target=self.update_monitor, daemon=True)
        self.update_thread.start()
        print("Update thread started")
        
        logging.info("GUI Monitor initialized successfully")
        print("Monitor initialization complete")

    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Progress section
        ttk.Label(main_frame, text="Progress:").grid(row=0, column=0, sticky=tk.W)
        self.progress_var = tk.StringVar(value="0.0%")
        ttk.Label(main_frame, textvariable=self.progress_var).grid(row=0, column=1, sticky=tk.W)
        
        # Detections section
        ttk.Label(main_frame, text="Detections:").grid(row=1, column=0, sticky=tk.W)
        self.detections_var = tk.StringVar(value="0")
        ttk.Label(main_frame, textvariable=self.detections_var).grid(row=1, column=1, sticky=tk.W)
        
        # FPS section
        ttk.Label(main_frame, text="FPS:").grid(row=2, column=0, sticky=tk.W)
        self.fps_var = tk.StringVar(value="0.0")
        ttk.Label(main_frame, textvariable=self.fps_var).grid(row=2, column=1, sticky=tk.W)
        
        # CPU Usage section
        ttk.Label(main_frame, text="CPU Usage:").grid(row=3, column=0, sticky=tk.W)
        self.cpu_var = tk.StringVar(value="0.0%")
        ttk.Label(main_frame, textvariable=self.cpu_var).grid(row=3, column=1, sticky=tk.W)
        
        # Memory Usage section
        ttk.Label(main_frame, text="Memory Usage:").grid(row=4, column=0, sticky=tk.W)
        self.memory_var = tk.StringVar(value="0.0%")
        ttk.Label(main_frame, textvariable=self.memory_var).grid(row=4, column=1, sticky=tk.W)
        
        # GPU Usage section
        ttk.Label(main_frame, text="GPU Usage:").grid(row=5, column=0, sticky=tk.W)
        self.gpu_var = tk.StringVar(value="0.0%")
        ttk.Label(main_frame, textvariable=self.gpu_var).grid(row=5, column=1, sticky=tk.W)
        
        # Status section
        ttk.Label(main_frame, text="Status:").grid(row=6, column=0, sticky=tk.W)
        self.status_var = tk.StringVar(value="Initializing...")
        ttk.Label(main_frame, textvariable=self.status_var).grid(row=6, column=1, sticky=tk.W)
        
        # Last update time
        ttk.Label(main_frame, text="Last Update:").grid(row=7, column=0, sticky=tk.W)
        self.time_var = tk.StringVar(value="-")
        ttk.Label(main_frame, textvariable=self.time_var).grid(row=7, column=1, sticky=tk.W)

    def get_gpu_usage(self):
        try:
            if self.handle:
                info = pynvml.nvmlDeviceGetUtilizationRates(self.handle)
                return info.gpu
            return 0
        except Exception as e:
            logging.error(f"GPU usage error: {str(e)}")
            return 0

    def read_progress(self):
        try:
            log_file = os.path.join('d:', 'logs', 'progress.log')
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r') as f:
                        data = json.load(f)
                        return data
                except Exception as e:
                    logging.error(f"Error reading progress file: {str(e)}")
            return None
        except Exception as e:
            logging.error(f"Progress reading error: {str(e)}")
            return None

    def update_monitor(self):
        while True:
            try:
                # Read progress from log file
                self.read_progress()

                # Get CPU usage
                try:
                    self.cpu_usage = psutil.cpu_percent(interval=0.1)
                except Exception as e:
                    logging.error(f"CPU monitoring error: {str(e)}")
                    self.cpu_usage = 0
                
                # Get memory usage
                try:
                    # Get system memory usage
                    mem = psutil.virtual_memory()
                    self.memory_usage = mem.percent
                    
                    # Also get process memory usage
                    process = psutil.Process()
                    mem_info = process.memory_info()
                    process_mem_mb = mem_info.rss / (1024 * 1024)
                    self.memory_var.set(f"{self.memory_usage:.1f}% (Process: {process_mem_mb:.1f} MB)")
                except Exception as e:
                    logging.error(f"Memory monitoring error: {str(e)}")
                    self.memory_usage = 0
                
                # Get GPU usage
                if self.handle:
                    try:
                        info = pynvml.nvmlDeviceGetUtilizationRates(self.handle)
                        self.gpu_usage = info.gpu
                    except Exception as e:
                        logging.error(f"GPU monitoring error: {str(e)}")
                        self.gpu_usage = 0
                
                # Update GUI
                self.root.after(0, self.update_gui)
                
                # Wait a bit before next update
                time.sleep(0.5)
                
                # Update last update time
                self.last_update = datetime.now()
                
            except Exception as e:
                logging.error(f"Monitor update error: {str(e)}")
                self.status_var.set(f"Error: {str(e)}")
                time.sleep(1)

    def update_gui(self):
        try:
            # Update metrics display
            self.progress_var.set(f"{self.progress:.1f}%")
            self.detections_var.set(str(self.detections))
            self.fps_var.set(f"{self.fps:.1f}")
            self.cpu_var.set(f"{self.cpu_usage:.1f}%")
            self.memory_var.set(f"{self.memory_usage:.1f}%")
            self.gpu_var.set(f"{self.gpu_usage:.1f}%")
            self.time_var.set(self.last_update.strftime('%H:%M:%S'))
            self.status_var.set("Running")
            
            
            # Clear previous lines
            self.canvas.delete('line')
            
            # Calculate scaling
            max_value = max(
                max(self.progress_history),
                max(self.detections_history),
                max(self.fps_history),
                max(self.cpu_history),
                max(self.gpu_history)
            )
            
            if max_value == 0: max_value = 100  # Prevent division by zero
            
            # Draw lines
            colors = ['blue', 'green', 'orange', 'purple', 'red']
            metrics = [
                (self.progress_history, 'Progress'),
                (self.detections_history, 'Detections'),
                (self.fps_history, 'FPS'),
                (self.cpu_history, 'CPU Usage'),
                (self.gpu_history, 'GPU Usage')
            ]
            
            for i, (data, label) in enumerate(metrics):
                points = []
                for j, value in enumerate(data):
                    x = 50 + (500 * j / (len(data) - 1))
                    y = 250 - (200 * value / max_value)
                    points.extend([x, y])
                
                # Draw line
                self.canvas.create_line(points, fill=colors[i], width=2, tags='line')
                
                # Add label
                self.canvas.create_text(
                    550, 250 - (200 * value / max_value),
                    text=label,
                    fill=colors[i],
                    anchor='e'
                )
            
        except Exception as e:
            logging.error(f"GUI update error: {str(e)}")

def main():
    root = tk.Tk()
    monitor = Monitor(root)
    # Start main loop
    root.mainloop()

if __name__ == '__main__':
    try:
        print("Starting GUI Monitor")
        logging.info("Starting GUI Monitor")
        
        # Check if required modules are installed
        try:
            import tkinter as tk
            from tkinter import ttk
            print("tkinter loaded successfully")
        except ImportError as e:
            print(f"Error: Missing tkinter module - {str(e)}")
            logging.error(f"Missing tkinter module: {str(e)}")
            raise
        
        # Create root window
        root = tk.Tk()
        print("Created root window")
        
        # Create monitor
        monitor = Monitor(root)
        print("Created monitor instance")
        
        # Start main loop
        print("Starting main loop")
        root.mainloop()
        
    except Exception as e:
        print(f"\nGUI Monitor crashed: {str(e)}")
        print("\nError details:")
        print(traceback.format_exc())
        logging.error(f"GUI Monitor crashed: {str(e)}")
        logging.error(traceback.format_exc())
        raise
