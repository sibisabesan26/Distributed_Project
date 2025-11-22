import dash
from dash import dcc, html
import requests
import plotly.graph_objs as go
from dash.dependencies import Input, Output

# Initialize Dash app
app = dash.Dash(__name__)
server = app.server  # for deployment if needed

# Layout
app.layout = html.Div([
    html.H1("Distributed Air Traffic Control Dashboard"),

    # Aircraft scatter plot
    dcc.Graph(id='aircraft-plot'),

    # Auto-refresh every 1 second
    dcc.Interval(
        id='interval-component',
        interval=1000,  # 1000 ms = 1 second
        n_intervals=0
    ),

    html.H2("Controller States"),
    html.Ul(id='node-states'),

    html.H2("Message Log (last 10 events)"),
    html.Ul(id='message-log')
])

# -----------------------------
# Update aircraft scatter plot
# -----------------------------
@app.callback(
    Output('aircraft-plot', 'figure'),
    Input('interval-component', 'n_intervals')
)
def update_plot(n):
    try:
        aircraft = requests.get("http://localhost:5000/aircraft").json()
    except:
        aircraft = []

    x = [a["pos"][0] for a in aircraft]
    y = [a["pos"][1] for a in aircraft]
    ids = [a["id"] for a in aircraft]

    trace = go.Scatter(
        x=x,
        y=y,
        mode='markers+text',
        text=ids,
        textposition='top center',
        marker=dict(size=12, color='blue')
    )

    layout = go.Layout(
        title="Aircraft Positions (Live)",
        xaxis=dict(range=[0, 600], title="X"),
        yaxis=dict(range=[0, 400], title="Y"),
        height=500
    )

    return go.Figure(data=[trace], layout=layout)

# -----------------------------
# Update node states
# -----------------------------
@app.callback(
    Output('node-states', 'children'),
    Input('interval-component', 'n_intervals')
)
def update_nodes(n):
    try:
        nodes = requests.get("http://localhost:5000/nodes").json()
    except:
        nodes = {}

    return [html.Li(f"Node {id}: {state['state']}") for id, state in nodes.items()]

# -----------------------------
# Update message log
# -----------------------------
@app.callback(
    Output('message-log', 'children'),
    Input('interval-component', 'n_intervals')
)
def update_logs(n):
    try:
        logs = requests.get("http://localhost:5000/logs").json()
    except:
        logs = []

    # Show last 10 events
    return [html.Li(f"{log['event']} - Node {log['node']} - Aircraft {log['aircraft']}") for log in logs[-10:]]

# -----------------------------
# Entry point
# -----------------------------
if __name__ == "__main__":
    app.run(port=8050, debug=True)
