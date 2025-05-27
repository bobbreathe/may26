import os
import time
import psutil
import pynvml
import json
import threading
from datetime import datetime
import traceback
import logging
import sys

# Set up logging with maximum detail
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('d:', 'logs', 'monitoring.log'), mode='w'),
        logging.StreamHandler()
    ]
)

# Add detailed formatter
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(filename)s:%(lineno)d'
)

# Get the root logger
root_logger = logging.getLogger()
for handler in root_logger.handlers:
    handler.setFormatter(formatter)

# Set up specific loggers
pynvml_logger = logging.getLogger('pynvml')
pynvml_logger.setLevel(logging.DEBUG)

psutil_logger = logging.getLogger('psutil')
psutil_logger.setLevel(logging.DEBUG)

class ConsoleMonitor:
    def __init__(self):
        try:
            self.progress = 0
            self.detections = 0
            self.fps = 0
            self.gpu_usage = 0
            self.last_update = datetime.now()
            self.update_interval = 1  # seconds
            
            # Initialize GPU monitoring
            try:
                pynvml.nvmlInit()
                self.handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            except Exception as e:
                self.handle = None
                logging.warning(f"GPU monitoring initialization error: {str(e)}")
                print("GPU monitoring not available")
            
            logging.info("ConsoleMonitor initialized successfully")
        except Exception as e:
            logging.error(f"Initialization error: {str(e)}")
            logging.error(traceback.format_exc())
            raise
    
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
    
    def update(self):
        try:
            while True:
                try:
                    data = self.read_progress()
                    if data:
                        self.progress = data.get('progress', 0)
                        self.detections = data.get('detections', 0)
                        self.fps = data.get('fps', 0)
                    
                    self.gpu_usage = self.get_gpu_usage()
                    
                    # Clear screen and print status
                    os.system('cls' if os.name == 'nt' else 'clear')
                    print("\nVideo Processing Monitor\n")
                    print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
                    print("-" * 50)
                    print(f"Progress: {self.progress:.1f}%")
                    print(f"Detections: {self.detections}")
                    print(f"FPS: {self.fps:.1f}")
                    print(f"GPU Usage: {self.gpu_usage:.1f}%")
                    print("-" * 50)
                    
                    time.sleep(self.update_interval)
                except KeyboardInterrupt:
                    logging.info("Monitor stopped by user")
                    break
                except Exception as e:
                    logging.error(f"Update error: {str(e)}")
                    logging.error(traceback.format_exc())
                    print(f"Error updating monitor: {str(e)}")
                    time.sleep(1)
        except Exception as e:
            logging.error(f"Main monitor error: {str(e)}")
            logging.error(traceback.format_exc())
            raise

def main():
    print("\n" * 100)  # Clear screen
    print("Starting console monitor script")
    print(f"Python version: {sys.version}")
    print(f"Current directory: {os.getcwd()}")
    
    try:
        print("\nInitializing logging...")
        logging.info("Starting console monitor script")
        print("\nCreating monitor instance...")
        monitor = ConsoleMonitor()
        print("\nStarting update loop...")
        monitor.update()
    except ImportError as e:
        print(f"\nImport error: {str(e)}")
        print("\nFailed to import required modules")
        print("\nInstalled packages:")
        try:
            import pkg_resources
            installed_packages = pkg_resources.working_set
            installed_packages_list = sorted(["%s==%s" % (i.key, i.version)
                                             for i in installed_packages])
            for package in installed_packages_list:
                print(package)
        except:
            print("Could not list installed packages")
    except Exception as e:
        print(f"\nMonitor crashed with error: {str(e)}")
        print("\nError details:")
        print(traceback.format_exc())
        logging.error(f"Monitor crashed: {str(e)}")
        logging.error(traceback.format_exc())
        raise
    finally:
        print("\nScript execution completed")

if __name__ == '__main__':
    main()
