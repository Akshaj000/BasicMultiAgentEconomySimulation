import mesa
import numpy as np
from mesa.space import MultiGrid
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector
from agents.central_bank import CentralBank
from agents.bank import Bank
from agents.household import Household
from agents.firm import Firm

class EconomyModel(mesa.Model):
    def __init__(self, N):
        self.num_agents = N
        self.grid = MultiGrid(20, 20, True)
        self.schedule = RandomActivation(self)
        self.total_liquidity = 100000
        
        # Initialize Central Bank
        self.central_bank = CentralBank(0, self)
        self.schedule.add(self.central_bank)
        self.grid.place_agent(self.central_bank, (0, 0))
        
        # Initialize Banks
        self.banks = []
        for i in range(1, 3):
            bank = Bank(i, self)
            self.banks.append(bank)
            self.schedule.add(bank)
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(bank, (x, y))
        
        # Initialize Households
        self.households = []
        for i in range(3, int(N/2)):
            household = Household(i, self)
            self.households.append(household)
            self.schedule.add(household)
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(household, (x, y))
        
        # Initialize Firms
        self.firms = []
        for i in range(int(N/2), N):
            firm = Firm(i, self)
            self.firms.append(firm)
            self.schedule.add(firm)
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(firm, (x, y))

        # Data Collection
        self.datacollector = DataCollector(
            model_reporters={
                "Inflation Rate": lambda m: m.central_bank.inflation_rate,
                "Lending Rate": lambda m: m.central_bank.lending_rate,
                "Total Money Supply": lambda m: m.total_liquidity,
                "Average Household Happiness": lambda m: np.mean([h.happiness for h in m.households]),
                "Total Production": lambda m: sum([f.inventory for f in m.firms]),
                "Average Household Debt": lambda m: np.mean([h.debt for h in m.households]),
                "Average Firm Money": lambda m: np.mean([f.money for f in m.firms]),
                "Average Household Money": lambda m: np.mean([h.money for h in m.households]),
                "Total Bank Profits": lambda m: sum([b.profits for b in m.banks])
            }
        )

    def step(self):
        self.datacollector.collect(self)
        self.schedule.step()
