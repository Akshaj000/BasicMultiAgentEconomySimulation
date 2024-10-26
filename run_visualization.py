import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import ipywidgets as widgets
from IPython.display import display
import numpy as np
from matplotlib.gridspec import GridSpec
from economy_model import EconomyModel

class EconomyVisualization:
    def __init__(self):
        self.create_controls()
        self.paused = False
        self.model = None
        self.init_simulation()

    def create_controls(self):
        self.money_supply_slider = widgets.FloatSlider(
            value=1000000,
            min=100000,
            max=5000000,
            step=100000,
            description='Money Supply:',
            style={'description_width': 'initial'}
        )
        
        self.interest_rate_slider = widgets.FloatSlider(
            value=0.05,
            min=0.01,
            max=0.20,
            step=0.01,
            description='Interest Rate:',
            style={'description_width': 'initial'}
        )
        
        self.firm_capital_slider = widgets.FloatSlider(
            value=100000,
            min=10000,
            max=500000,
            step=10000,
            description='Initial Firm Capital:',
            style={'description_width': 'initial'}
        )
        
        self.consumer_money_slider = widgets.FloatSlider(
            value=1000,
            min=100,
            max=10000,
            step=100,
            description='Initial Consumer Money:',
            style={'description_width': 'initial'}
        )
        
        self.num_firms_slider = widgets.IntSlider(
            value=10,
            min=5,
            max=50,
            step=5,
            description='Number of Firms:',
            style={'description_width': 'initial'}
        )
        
        self.num_consumers_slider = widgets.IntSlider(
            value=100,
            min=50,
            max=500,
            step=50,
            description='Number of Consumers:',
            style={'description_width': 'initial'}
        )
        
        self.pause_button = widgets.Button(description='Pause/Resume')
        self.reset_button = widgets.Button(description='Reset Simulation')
        
        # Layout the controls
        self.controls = widgets.VBox([
            widgets.HBox([self.money_supply_slider, self.interest_rate_slider]),
            widgets.HBox([self.firm_capital_slider, self.consumer_money_slider]),
            widgets.HBox([self.num_firms_slider, self.num_consumers_slider]),
            widgets.HBox([self.pause_button, self.reset_button])
        ])
        
        # Add button callbacks
        self.pause_button.on_click(self.toggle_pause)
        self.reset_button.on_click(self.reset_simulation)

        # Add slider callbacks to update simulation dynamically
        for slider in [
            self.money_supply_slider,
            self.interest_rate_slider,
            self.firm_capital_slider,
            self.consumer_money_slider,
            self.num_firms_slider,
            self.num_consumers_slider,
        ]:
            slider.observe(self.update_simulation_params, names='value')

    def toggle_pause(self, _):
        self.paused = not self.paused

    def reset_simulation(self, _):
        self.init_simulation()

    def init_simulation(self):
        self.model = EconomyModel(
            num_consumers=self.num_consumers_slider.value,
            num_firms=self.num_firms_slider.value,
            initial_money_supply=self.money_supply_slider.value,
            base_interest_rate=self.interest_rate_slider.value,
            initial_firm_capital=self.firm_capital_slider.value,
            initial_consumer_money=self.consumer_money_slider.value
        )
        
        # Initialize plots
        plt.close('all')
        self.fig = plt.figure(figsize=(15, 10))
        gs = GridSpec(3, 2, figure=self.fig)
        
        # Create subplots with GridSpec
        self.ax1 = self.fig.add_subplot(gs[0, 0])  # Inflation Rate
        self.ax2 = self.fig.add_subplot(gs[0, 1])  # Employment & Satisfaction
        self.ax3 = self.fig.add_subplot(gs[1, 0])  # Bankruptcies
        self.ax4 = self.fig.add_subplot(gs[1, 1])  # Money Supply & Loans
        self.ax5 = self.fig.add_subplot(gs[2, :])  # Price Levels
        
        # Initialize data storage
        self.data = {
            'steps': [],
            'inflation': [],
            'employment': [],
            'satisfaction': [],
            'bankruptcies_firms': [],
            'bankruptcies_consumers': [],
            'money_supply': [],
            'total_loans': [],
            'average_price': [],
            'price_range': []
        }

    def update_simulation_params(self, change):
        # Update model parameters based on slider values without reinitializing the simulation
        self.model.num_consumers = self.num_consumers_slider.value
        self.model.num_firms = self.num_firms_slider.value
        self.model.central_bank.money_supply = self.money_supply_slider.value
        self.model.central_bank.base_interest_rate = self.interest_rate_slider.value
        self.model.initial_firm_capital = self.firm_capital_slider.value
        self.model.initial_consumer_money = self.consumer_money_slider.value

    def update(self, frame):
        if not self.paused:
            # Update model
            self.model.step()
            
            # Collect data
            self.data['steps'].append(frame)
            self.data['inflation'].append(self.model.central_bank.inflation_rate)
            self.data['employment'].append(self.model.get_employment_rate() * 100)
            self.data['satisfaction'].append(self.model.get_average_satisfaction())
            self.data['bankruptcies_firms'].append(self.model.central_bank.bankrupted_firms)
            self.data['bankruptcies_consumers'].append(self.model.central_bank.bankrupted_consumers)
            self.data['money_supply'].append(self.model.central_bank.money_supply)
            self.data['total_loans'].append(self.model.central_bank.total_loans)
            
            # Calculate price statistics
            prices = [f.price for f in self.model.get_firms()]
            avg_price = np.mean(prices) if prices else 0
            price_range = np.std(prices) if prices else 0
            self.data['average_price'].append(avg_price)
            self.data['price_range'].append(price_range)
            
            # Update plots
            self.update_plots()

    def update_plots(self):
        # Clear all axes
        for ax in [self.ax1, self.ax2, self.ax3, self.ax4, self.ax5]:
            ax.clear()
            
        steps = self.data['steps']
        
        # Plot 1: Inflation Rate
        self.ax1.plot(steps, self.data['inflation'], 'r-')
        self.ax1.set_title('Inflation Rate')
        self.ax1.set_ylabel('Rate (%)')
        
        # Plot 2: Employment & Satisfaction
        self.ax2.plot(steps, self.data['employment'], 'b-', label='Employment')
        self.ax2.plot(steps, self.data['satisfaction'], 'g-', label='Satisfaction')
        self.ax2.set_title('Employment & Satisfaction')
        self.ax2.set_ylabel('Percentage')
        self.ax2.legend()
        
        # Plot 3: Bankruptcies
        self.ax3.plot(steps, self.data['bankruptcies_firms'], 'r-', label='Firms')
        self.ax3.plot(steps, self.data['bankruptcies_consumers'], 'b-', label='Consumers')
        self.ax3.set_title('Cumulative Bankruptcies')
        self.ax3.legend()
        
        # Plot 4: Money Supply & Loans
        self.ax4.plot(steps, self.data['money_supply'], 'g-', label='Money Supply')
        self.ax4.plot(steps, self.data['total_loans'], 'y-', label='Total Loans')
        self.ax4.set_title('Money Supply & Loans')
        self.ax4.legend()
        
        # Plot 5: Price Levels with Variance
        avg_price = self.data['average_price']
        price_range = self.data['price_range']
        self.ax5.plot(steps, avg_price, 'b-', label='Average Price')
        self.ax5.fill_between(steps, 
                            [a - r for a, r in zip(avg_price, price_range)],
                            [a + r for a, r in zip(avg_price, price_range)],
                            alpha=0.2)
        self.ax5.set_title('Price Levels (with variance)')
        self.ax5.legend()
        
        plt.tight_layout()

    def run(self, steps=200, num_consumers=None, num_firms=None, 
            initial_money_supply=None, base_interest_rate=None, 
            initial_firm_capital=None, initial_consumer_money=None):
        # Update slider values if parameters are provided
        if num_consumers is not None:
            self.num_consumers_slider.value = num_consumers
        if num_firms is not None:
            self.num_firms_slider.value = num_firms
        if initial_money_supply is not None:
            self.money_supply_slider.value = initial_money_supply
        if base_interest_rate is not None:
            self.interest_rate_slider.value = base_interest_rate
        if initial_firm_capital is not None:
            self.firm_capital_slider.value = initial_firm_capital
        if initial_consumer_money is not None:
            self.consumer_money_slider.value = initial_consumer_money

        display(self.controls)
        self.init_simulation()
        
        anim = FuncAnimation(self.fig, self.update, frames=steps, interval=100, repeat=False)
        plt.show()
        
        return self.model

def run_simulation(steps=200, num_consumers=None, num_firms=None,
                  initial_money_supply=None, base_interest_rate=None,
                  initial_firm_capital=None, initial_consumer_money=None):
    vis = EconomyVisualization()
    return vis.run(
        steps=steps,
        num_consumers=num_consumers,
        num_firms=num_firms,
        initial_money_supply=initial_money_supply,
        base_interest_rate=base_interest_rate,
        initial_firm_capital=initial_firm_capital,
        initial_consumer_money=initial_consumer_money
    )

# Make run_simulation available when importing this module
__all__ = ['run_simulation']
