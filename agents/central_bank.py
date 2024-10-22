import mesa

class CentralBank(mesa.Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.lending_rate = 0.05
        self.inflation_rate = 0.02
        self.money_supply = model.total_liquidity
        self.pos = (0, 0)

    def adjust_lending_rate(self):
        if self.inflation_rate > 0.02:
            self.lending_rate = min(0.15, self.lending_rate + 0.01)
        elif self.inflation_rate < 0.02:
            self.lending_rate = max(0.01, self.lending_rate - 0.01)

    def calculate_inflation(self):
        old_money_supply = self.money_supply
        self.money_supply = self.model.total_liquidity
        if old_money_supply > 0:
            self.inflation_rate = (self.money_supply - old_money_supply) / old_money_supply

    def step(self):
        self.calculate_inflation()
        self.adjust_lending_rate()
        if self.model.total_liquidity < 5000:
            self.model.total_liquidity += 1000
