import os
import sys
import threading
import time

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import both scripts
def run_monitor():
    import console_monitor
    console_monitor.main()

def run_processor():
    import food_sampling_detector
    food_sampling_detector.main()

if __name__ == '__main__':
    print("Starting both scripts...")
    
    # Start both scripts in separate threads
    monitor_thread = threading.Thread(target=run_monitor)
    processor_thread = threading.Thread(target=run_processor)
    
    monitor_thread.start()
    processor_thread.start()
    
    # Wait for both threads to finish
    monitor_thread.join()
    processor_thread.join()
