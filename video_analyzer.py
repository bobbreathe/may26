import os
import openai
from moviepy.editor import VideoFileClip
import pandas as pd
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Set up OpenAI API
openai.api_key = os.getenv('OPENAI_API_KEY')

# Constants
VIDEO_INPUT_DIR = os.path.join('d:', 'Input_videos')
ANALYSIS_OUTPUT_DIR = os.path.join('d:', 'processed_videos')

# Create output directory if it doesn't exist
os.makedirs(ANALYSIS_OUTPUT_DIR, exist_ok=True)

def analyze_video(video_path):
    try:
        # Extract video properties
        clip = VideoFileClip(video_path)
        duration = clip.duration
        fps = clip.fps
        resolution = f"{clip.w}x{clip.h}"
        
        # Get video name without extension
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        
        # Prepare video analysis prompt
        prompt = f"""Analyze this video:
        - Duration: {duration:.2f} seconds
        - FPS: {fps}
        - Resolution: {resolution}
        
        Please provide a detailed analysis of the video content, including:
        1. Main subjects/objects in the video
        2. Potential use cases or applications
        3. Technical considerations
        4. Any potential issues or limitations
        
        Format the response as JSON with these fields:
        {{
            "video_name": "{video_name}",
            "duration": {duration},
            "fps": {fps},
            "resolution": "{resolution}",
            "analysis": {{
                "subjects": [],
                "use_cases": [],
                "technical_considerations": [],
                "issues": []
            }}
        }}
        """
        
        # Get analysis from OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a video analysis expert."},
                {"role": "user", "content": prompt}
            ]
        )
        
        # Parse the response
        analysis = json.loads(response.choices[0].message.content)
        
        # Save analysis to file
        output_path = os.path.join(ANALYSIS_OUTPUT_DIR, f"{video_name}_analysis.json")
        with open(output_path, 'w') as f:
            json.dump(analysis, f, indent=4)
        
        print(f"Analysis complete for {video_name}")
        return analysis
        
    except Exception as e:
        print(f"Error analyzing {video_path}: {str(e)}")
        return None

def main():
    # Get list of video files
    video_files = [f for f in os.listdir(VIDEO_INPUT_DIR) if f.endswith('.mp4')]
    
    if not video_files:
        print("No video files found in the input directory")
        return
    
    # Process each video
    for video_file in video_files:
        video_path = os.path.join(VIDEO_INPUT_DIR, video_file)
        analysis = analyze_video(video_path)
        
        if analysis:
            # Print summary
            print(f"\nAnalysis for {analysis['video_name']}:")
            print(f"Duration: {analysis['duration']:.2f} seconds")
            print(f"FPS: {analysis['fps']}")
            print(f"Resolution: {analysis['resolution']}")
            print("\nKey Points:")
            for key, value in analysis['analysis'].items():
                print(f"\n{key.replace('_', ' ').title()}")
                for item in value:
                    print(f"- {item}")

if __name__ == "__main__":
    main()
