import mesa
from .household import Household
from .firm import Firm

class Bank(mesa.Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.liquidity = model.total_liquidity / 2
        self.loans_outstanding = 0
        self.profits = 0

    def maintain_liquidity(self):
        if self.liquidity < 1000:
            borrowed = min(1000, self.model.total_liquidity * 0.1)
            self.liquidity += borrowed
            self.model.total_liquidity -= borrowed

    def provide_loans(self): 
        lending_capacity = self.liquidity * 0.8
        for agent in self.model.schedule.agents:
            if isinstance(agent, (Household, Firm)) and lending_capacity > 0:
                loan_amount = min(500, lending_capacity)
                agent.borrow(loan_amount, self.model.central_bank.lending_rate)
                self.loans_outstanding += loan_amount
                self.liquidity -= loan_amount
                lending_capacity -= loan_amount

    def collect_interest(self):
        interest_income = self.loans_outstanding * self.model.central_bank.lending_rate
        self.profits += interest_income
        self.liquidity += interest_income

    def step(self):
        self.maintain_liquidity()
        self.provide_loans()
        self.collect_interest()