from mesa.visualization.modules import ChartModule
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import TextElement
from economy_model import EconomyModel

class EconomicIndicatorText(TextElement):
    def __init__(self):
        pass

    def render(self, model):
        inflation_rate = model.central_bank.inflation_rate * 100
        lending_rate = model.central_bank.lending_rate * 100
        money_supply = model.total_liquidity
        avg_happiness = sum(h.happiness for h in model.households) / len(model.households)
        
        return f"Inflation Rate: {inflation_rate:.2f}%<br>" \
               f"Lending Rate: {lending_rate:.2f}%<br>" \
               f"Money Supply: ${money_supply:,.2f}<br>" \
               f"Average Happiness: {avg_happiness:.2f}"


def create_economy_visualization():
    
    chart_elements = [
        ChartModule([
            {"Label": "Inflation Rate", "Color": "Red"},
            {"Label": "Lending Rate", "Color": "Blue"}
        ]),
        
        ChartModule([
            {"Label": "Total Money Supply", "Color": "Green"},
            {"Label": "Average Household Happiness", "Color": "Yellow"}
        ]),
        
        ChartModule([
            {"Label": "Total Production", "Color": "Purple"},
            {"Label": "Average Household Debt", "Color": "Orange"}
        ]),
        
        ChartModule([
            {"Label": "Average Firm Money", "Color": "Brown"},
            {"Label": "Total Bank Profits", "Color": "Black"}
        ])
    ]
    
    # Add text element for current statistics
    text_element = EconomicIndicatorText()
    
    # Combine all elements
    elements = [text_element] + chart_elements
    
    # Create and return server
    server = ModularServer(
        EconomyModel,
        elements,
        "Economy Model",
        {"N": 20}
    )
    return server

if __name__ == '__main__':
    server = create_economy_visualization()
    server.launch()