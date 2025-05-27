import cv2
import numpy as np
import tensorflow as tf
from moviepy.editor import VideoFileClip
import os
import time
from datetime import timedelta
import traceback
import logging

# Set up logging with maximum detail
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('d:', 'logs', 'video_processing.log'), mode='w'),
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
tf_logger = logging.getLogger('tensorflow')
tf_logger.setLevel(logging.DEBUG)

cv2_logger = logging.getLogger('cv2')
cv2_logger.setLevel(logging.DEBUG)

moviepy_logger = logging.getLogger('moviepy')
moviepy_logger.setLevel(logging.DEBUG)

class FoodSamplingDetector:
    def __init__(self):
        try:
            # Load face and hand detection models
            self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            self.hand_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_hand.xml')
            
            # Initialize GPU configuration
            gpus = tf.config.experimental.list_physical_devices('GPU')
            if gpus:
                try:
                    tf.config.experimental.set_memory_growth(gpus[0], True)
                except RuntimeError as e:
                    logging.error(f"GPU configuration error: {str(e)}")
                    print(f"GPU configuration error: {str(e)}")
            
            self.face_threshold = 0.3
            self.hand_threshold = 0.3
            self.min_face_size = 50
            self.min_hand_size = 30
            self.prev_face = None
            self.prev_hand = None
            self.prev_frame = None
            self.frame_count = 0
            self.frame_times = []
            
            # Create logs directory if it doesn't exist
            os.makedirs(os.path.join('d:', 'logs'), exist_ok=True)
            
            logging.info("FoodSamplingDetector initialized successfully")
            print("FoodSamplingDetector initialized successfully")
        except Exception as e:
            print(f"\nInitialization error: {str(e)}")
            print("\nError details:")
            print(traceback.format_exc())
            logging.error(f"Initialization error: {str(e)}")
            logging.error(traceback.format_exc())
            raise
        finally:
            print("\nInitialization complete")
        
    def detect_face(self, frame):
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(self.min_face_size, self.min_face_size)
            )
            return faces
        except Exception as e:
            logging.error(f"Face detection error: {str(e)}")
            return []
    
    def detect_hand(self, frame):
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            hands = self.hand_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(self.min_hand_size, self.min_hand_size)
            )
            return hands
        except Exception as e:
            logging.error(f"Hand detection error: {str(e)}")
            return []
    
    def is_hand_approaching_face(self, face, hand):
        if len(face) == 0 or len(hand) == 0:
            return False
            
        (fx, fy, fw, fh) = face[0]
        (hx, hy, hw, hh) = hand[0]
        
        # Calculate distance between hand and face
        face_center = (fx + fw//2, fy + fh//2)
        hand_center = (hx + hw//2, hy + hh//2)
        distance = np.sqrt((face_center[0] - hand_center[0])**2 + 
                         (face_center[1] - hand_center[1])**2)
        
        # Check if hand is moving towards face
        if self.prev_hand is not None and self.prev_face is not None:
            prev_distance = np.sqrt((self.prev_face[0] + self.prev_face[2]//2 - 
                                   self.prev_hand[0] - self.prev_hand[2]//2)**2 +
                                  (self.prev_face[1] + self.prev_face[3]//2 - 
                                   self.prev_hand[1] - self.prev_hand[3]//2)**2)
            
            # Hand is moving towards face if distance is decreasing
            if distance < prev_distance:
                return True
        
        self.prev_face = (fx, fy, fw, fh)
        self.prev_hand = (hx, hy, hw, hh)
        return False
    
    def process_video(self, input_path, output_path):
        # Get video info
        clip = VideoFileClip(input_path)
        self.fps = clip.fps
        
        # Create output video
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, self.fps, 
                            (int(clip.w), int(clip.h)))
        
        # Process frames
        frame_count = 0
        buffer = []
        buffer_start_time = None
        
        for frame in clip.iter_frames():
            frame_count += 1
            
            # Detect face and hand
            faces = self.detect_face(frame)
            hands = self.detect_hand(frame)
            
            # Check if hand is approaching face
            if self.is_hand_approaching_face(faces, hands):
                if buffer_start_time is None:
                    buffer_start_time = frame_count / self.fps
                buffer.append(frame)
            else:
                if buffer_start_time is not None:
                    # Process buffer if it's long enough
                    if len(buffer) >= self.fps:  # At least 1 second
                        start_time = max(0, buffer_start_time - 1)  # 1 second before
                        end_time = min(clip.duration, buffer_start_time + 10)  # 10 seconds after
                        
                        # Extract segment
                        segment = clip.subclip(start_time, end_time)
                        
                        # Write to output
                        segment.write_videofile(
                            output_path,
                            codec='libx264',
                            audio_codec='aac',
                            temp_audiofile='temp-audio.m4a',
                            remove_temp=True
                        )
                        
                    buffer = []
                    buffer_start_time = None
            
            # Update progress
            if frame_count % 100 == 0:
                progress = (frame_count / clip.duration * 100)
                print(f"Processing: {progress:.1f}%")
        
        # Clean up
        clip.close()
        out.release()
        cv2.destroyAllWindows()

def main():
    try:
        # Create output directory if it doesn't exist
        output_dir = os.path.join('d:', 'processed_videos')
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize detector
        detector = FoodSamplingDetector()
        
        # Process video
        input_path = os.path.join('d:', 'Input_videos', 'VID_20241020_095709_10_018.mp4')
        output_filename = f"PROCESSED_{os.path.basename(os.path.dirname(input_path))}_{os.path.basename(input_path)}"
        output_path = os.path.join(output_dir, output_filename)
        
        logging.info(f"Starting video analysis of {input_path}")
        start_time = time.time()
        
        detector.process_video(input_path, output_path)
        
        end_time = time.time()
        logging.info(f"Processing complete!")
        logging.info(f"Total time: {timedelta(seconds=end_time - start_time)}")
        logging.info(f"Output saved to: {output_path}")
        logging.info(f"Original file directory: {os.path.dirname(input_path)}")
        logging.info(f"Original file name: {os.path.basename(input_path)}")
    except Exception as e:
        logging.error(f"Main process error: {str(e)}")
        logging.error(traceback.format_exc())
        raise

if __name__ == "__main__":
    print("Starting video processing script")
    try:
        print("Initializing logging...")
        logging.info("Starting video processing script")
        print("Calling main()...")
        main()
    except Exception as e:
        print(f"Script crashed with error: {str(e)}")
        logging.error(f"Script crashed: {str(e)}")
        logging.error(traceback.format_exc())
        raise
