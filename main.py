# main.py
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import ChartModule, CanvasGrid
from mesa.visualization.UserParam import Slider
from agents import Firm, CentralBank, Consumer
from model import EconomyModel

def agent_portrayal(agent):
    portrayal = {"Shape": "circle", "Filled": "true", "r": 0.5}
    
    if isinstance(agent, Firm):
        if agent.bankrupt:
            portrayal["Color"] = "darkred"
            portrayal["r"] = 0.3
        else:
            capital_ratio = agent.capital / agent.initial_capital
            blue_intensity = max(0, min(255, int(capital_ratio * 255)))
            portrayal["Color"] = f"rgb(0,0,{blue_intensity})"
        portrayal["Layer"] = 1
        
    elif isinstance(agent, Consumer):
        if agent.bankrupt:
            portrayal["Color"] = "gray"
            portrayal["r"] = 0.3
        else:
            money_ratio = agent.money / agent.initial_money
            green_intensity = max(0, min(255, int(money_ratio * 255)))
            portrayal["Color"] = f"rgb(0,{green_intensity},0)"
        portrayal["Layer"] = 0
    
    return portrayal

grid = CanvasGrid(agent_portrayal, 20, 20, 600, 600)

charts = [
    ChartModule([
        {"Label": "Economic Health Index", "Color": "black"}
    ], data_collector_name="datacollector"),
    
    ChartModule([
        {"Label": "Inflation Rate", "Color": "red"},
        {"Label": "Employment Rate", "Color": "blue"},
        {"Label": "Average Credit Score", "Color": "purple"}
    ], data_collector_name="datacollector"),
    
    ChartModule([
        {"Label": "Average Satisfaction", "Color": "green"},
        {"Label": "Average Price", "Color": "orange"}
    ], data_collector_name="datacollector"),
    
    ChartModule([
        {"Label": "Money Supply", "Color": "purple"},
        {"Label": "Total Loans", "Color": "brown"}
    ], data_collector_name="datacollector"),
    
    ChartModule([
        {"Label": "Bankrupted Firms", "Color": "red"},
        {"Label": "Bankrupted Consumers", "Color": "gray"}
    ], data_collector_name="datacollector")
]

model_params = {
    "num_consumers": Slider(
        "Number of Consumers", 100, 10, 500, 10,
        description="Number of consumers in the economy"
    ),
    "num_firms": Slider(
        "Number of Firms", 20, 5, 100, 5,
        description="Number of firms in the economy"
    ),
    "initial_money_supply": Slider(
        "Initial Money Supply", 2000000, 500000, 10000000, 100000,
        description="Initial money supply in the economy"
    ),
    "base_interest_rate": Slider(
        "Base Interest Rate", 0.05, 0.01, 0.20, 0.01,
        description="Base interest rate set by central bank"
    ),
    "initial_firm_capital": Slider(
        "Initial Firm Capital", 200000, 50000, 1000000, 50000,
        description="Initial capital for each firm"
    ),
    "initial_consumer_money": Slider(
        "Initial Consumer Money", 2000, 500, 20000, 500,
        description="Initial money for each consumer"
    ),
    "market_volatility": Slider(
        "Market Volatility", 0.2, 0.0, 1.0, 0.05,
        description="Market price volatility (0 = stable, 1 = volatile)"
    ),
    "bankruptcy_threshold": Slider(
        "Bankruptcy Threshold", 0.3, 0.1, 0.9, 0.05,
        description="Capital ratio threshold for bankruptcy (lower = stricter)"
    ),
    "satisfaction_threshold": Slider(
        "Satisfaction Threshold", 0.5, 0.1, 0.9, 0.05,
        description="Consumer satisfaction threshold for loyalty"
    )
}

server = ModularServer(
    EconomyModel,
    [grid] + charts,
    "Advanced Economy Simulation",
    model_params
)

if __name__ == "__main__":
    server.launch()
