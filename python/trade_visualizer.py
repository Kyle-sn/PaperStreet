import pandas as pd
from plotly.subplots import make_subplots
import plotly.graph_objects as go

data = pd.read_csv('C:\\Users\\kylek\\data\\20240508_test.csv', index_col=False)

data['time'] = pd.to_datetime(data['time'], unit='ns')
data['time'] = data['time'].dt.tz_localize('UTC').dt.tz_convert('US/Central')
# data should be in the right order when written but doing this to be sure
data = data.sort_values(by='time')

fig = make_subplots(rows=2, cols=1,
                    subplot_titles=("PnL", "Position"),
                    row_heights=[0.8, 0.3],
                    shared_xaxes=True,
                    vertical_spacing=0.05)

fig.add_trace(go.Scatter(x=data['time'], y=data['cumulative_pnl']),row=1, col=1)
fig.add_trace(go.Scatter(x=data['time'], y=data['current_inventory_size']),row=2, col=1)

fig.update_layout(height=750, width=1000, title_text="Strategy Visualizer")

fig.show()
