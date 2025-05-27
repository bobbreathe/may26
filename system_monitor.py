import dash
from dash import dcc, html
from dash.dependencies import Output, Input
import plotly.graph_objects as go
import psutil
import time
import sys
import os
import pynvml
import threading

# Initialize NVML for GPU monitoring
try:
    pynvml.nvmlInit()
except pynvml.NVMLError:
    print("No NVIDIA GPU found")

# Get CPU information
try:
    cpu_info = psutil.cpu_count()
except:
    cpu_info = 'Unknown'

class SystemMonitor:
    def __init__(self):
        self.cpu_percent = []
        self.memory_percent = []
        self.gpu_percent = []
        self.cpu_temp = []
        self.timestamps = []
        self.max_points = 200

    def get_cpu_usage(self):
        return psutil.cpu_percent(interval=0.1)

    def get_memory_usage(self):
        mem = psutil.virtual_memory()
        return mem.percent

    def get_gpu_usage(self):
        try:
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            return pynvml.nvmlDeviceGetUtilizationRates(handle).gpu
        except:
            return 0

    def get_cpu_temperature(self):
        try:
            temps = psutil.sensors_temperatures()
            if 'coretemp' in temps:
                return temps['coretemp'][0].current
            return 0
        except:
            return 0

    def update_data(self):
        self.timestamps.append(time.strftime('%H:%M:%S'))
        self.cpu_percent.append(self.get_cpu_usage())
        self.memory_percent.append(self.get_memory_usage())
        self.gpu_percent.append(self.get_gpu_usage())
        self.cpu_temp.append(self.get_cpu_temperature())

        # Keep only the last max_points
        if len(self.timestamps) > self.max_points:
            self.timestamps.pop(0)
            self.cpu_percent.pop(0)
            self.memory_percent.pop(0)
            self.gpu_percent.pop(0)
            self.cpu_temp.pop(0)

# Initialize system monitor
monitor = SystemMonitor()

# Create Dash app
app = dash.Dash(__name__)

# Layout
app.layout = html.Div([
    html.H1('System Monitor', style={'textAlign': 'center'}),
    
    html.Div([
        html.H3(f'CPU: {cpu_info} cores'),
        dcc.Graph(id='cpu-graph'),
        dcc.Graph(id='memory-graph'),
        dcc.Graph(id='gpu-graph'),
        dcc.Graph(id='temp-graph')
    ], style={'padding': '20px'}),
    
    dcc.Interval(
        id='interval-component',
        interval=1000,  # update every second
        n_intervals=0
    )
])

# Update CPU graph
@app.callback(
    Output('cpu-graph', 'figure'),
    [Input('interval-component', 'n_intervals')]
)
def update_cpu_graph(n):
    monitor.update_data()
    return {
        'data': [go.Scatter(
            x=monitor.timestamps,
            y=monitor.cpu_percent,
            mode='lines',
            name='CPU Usage'
        )],
        'layout': {
            'title': 'CPU Usage (%)',
            'yaxis': {'range': [0, 100]},
            'height': 250
        }
    }

# Update memory graph
@app.callback(
    Output('memory-graph', 'figure'),
    [Input('interval-component', 'n_intervals')]
)
def update_memory_graph(n):
    return {
        'data': [go.Scatter(
            x=monitor.timestamps,
            y=monitor.memory_percent,
            mode='lines',
            name='Memory Usage'
        )],
        'layout': {
            'title': 'Memory Usage (%)',
            'yaxis': {'range': [0, 100]},
            'height': 250
        }
    }

# Update GPU graph
@app.callback(
    Output('gpu-graph', 'figure'),
    [Input('interval-component', 'n_intervals')]
)
def update_gpu_graph(n):
    return {
        'data': [go.Scatter(
            x=monitor.timestamps,
            y=monitor.gpu_percent,
            mode='lines',
            name='GPU Usage'
        )],
        'layout': {
            'title': 'GPU Usage (%)',
            'yaxis': {'range': [0, 100]},
            'height': 250
        }
    }

# Update temperature graph
@app.callback(
    Output('temp-graph', 'figure'),
    [Input('interval-component', 'n_intervals')]
)
def update_temp_graph(n):
    return {
        'data': [go.Scatter(
            x=monitor.timestamps,
            y=monitor.cpu_temp,
            mode='lines',
            name='CPU Temp'
        )],
        'layout': {
            'title': 'CPU Temperature (°C)',
            'yaxis': {'range': [0, 100]},
            'height': 250
        }
    }

if __name__ == '__main__':
    app.run_server(debug=True)
