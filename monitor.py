import dash
from dash import dcc, html
from dash.dependencies import Output, Input
import plotly.graph_objects as go
import psutil
import time
import threading
import os
import json

# Create Dash app
app = dash.Dash(__name__)

# Shared data structure
progress_data = {
    'timestamp': [],
    'progress': [],
    'detections': [],
    'fps': [],
    'gpu_usage': []
}

# Function to read progress from log file
def read_progress():
    log_file = os.path.join('d:', 'logs', 'progress.log')
    if not os.path.exists(log_file):
        return None
    
    with open(log_file, 'r') as f:
        try:
            return json.load(f)
        except:
            return None

# Update progress data
def get_gpu_usage():
    try:
        import pynvml
        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        info = pynvml.nvmlDeviceGetUtilizationRates(handle)
        return info.gpu
    except:
        return 0

def update_progress():
    while True:
        try:
            data = read_progress()
            if data:
                progress_data['timestamp'].append(time.strftime('%H:%M:%S'))
                progress_data['progress'].append(data.get('progress', 0))
                progress_data['detections'].append(data.get('detections', 0))
                progress_data['fps'].append(data.get('fps', 0))
                progress_data['gpu_usage'].append(get_gpu_usage())
                
                # Keep only last 100 points
                if len(progress_data['timestamp']) > 100:
                    for key in progress_data:
                        progress_data[key].pop(0)
        except:
            pass
        time.sleep(1)

# Start progress monitoring thread
threading.Thread(target=update_progress, daemon=True).start()

# Layout
app.layout = html.Div([
    html.H1('Video Processing Monitor', style={'textAlign': 'center'}),
    
    html.Div([
        dcc.Graph(id='progress-graph'),
        dcc.Graph(id='detections-graph'),
        dcc.Graph(id='fps-graph'),
        dcc.Graph(id='gpu-graph'),
        
        html.Div(id='status-text', style={'margin': '20px', 'fontSize': '20px'})
    ]),
    
    dcc.Interval(
        id='interval-component',
        interval=1000,  # update every second
        n_intervals=0
    )
])

# Update progress graph
@app.callback(
    Output('progress-graph', 'figure'),
    [Input('interval-component', 'n_intervals')]
)
def update_progress_graph(n):
    return {
        'data': [go.Scatter(
            x=progress_data['timestamp'],
            y=progress_data['progress'],
            mode='lines',
            name='Progress'
        )],
        'layout': {
            'title': 'Processing Progress (%)',
            'yaxis': {'range': [0, 100]},
            'height': 300
        }
    }

# Update detections graph
@app.callback(
    Output('detections-graph', 'figure'),
    [Input('interval-component', 'n_intervals')]
)
def update_detections_graph(n):
    return {
        'data': [go.Scatter(
            x=progress_data['timestamp'],
            y=progress_data['detections'],
            mode='lines',
            name='Detections'
        )],
        'layout': {
            'title': 'Food Sampling Detections',
            'height': 300
        }
    }

# Update FPS graph
@app.callback(
    Output('fps-graph', 'figure'),
    [Input('interval-component', 'n_intervals')]
)
def update_fps_graph(n):
    return {
        'data': [go.Scatter(
            x=progress_data['timestamp'],
            y=progress_data['fps'],
            mode='lines',
            name='FPS'
        )],
        'layout': {
            'title': 'Frames Per Second',
            'height': 300
        }
    }

# Update GPU usage graph
@app.callback(
    Output('gpu-graph', 'figure'),
    [Input('interval-component', 'n_intervals')]
)
def update_gpu_graph(n):
    return {
        'data': [go.Scatter(
            x=progress_data['timestamp'],
            y=progress_data['gpu_usage'],
            mode='lines',
            name='GPU Usage'
        )],
        'layout': {
            'title': 'GPU Usage (%)',
            'yaxis': {'range': [0, 100]},
            'height': 300
        }
    }

# Update status text
@app.callback(
    Output('status-text', 'children'),
    [Input('interval-component', 'n_intervals')]
)
def update_status(n):
    data = read_progress()
    if data:
        return [
            html.P(f"Current Progress: {data.get('progress', 0):.1f}%"),
            html.P(f"Total Detections: {data.get('detections', 0)}"),
            html.P(f"Current FPS: {data.get('fps', 0):.1f}"),
            html.P(f"GPU Usage: {get_gpu_usage():.1f}%")
        ]
    return [html.P("No data available yet")]

if __name__ == '__main__':
    app.run_server(debug=True, port=8050)
