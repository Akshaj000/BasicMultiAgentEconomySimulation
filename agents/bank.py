# bank.py
from mesa import Agent
import numpy as np
from agents.firm import Firm
from agents.consumer import Consumer

class CentralBank(Agent):
    def __init__(self, unique_id, model, initial_money_supply, base_interest_rate):
        super().__init__(unique_id, model)
        self.money_supply = initial_money_supply
        self.base_interest_rate = base_interest_rate
        self.total_loans = 0
        self.inflation_rate = 0
        self.bankrupted_firms = 0
        self.bankrupted_consumers = 0
        self.price_history = []
        
    def step(self):
        self.lend_to_agents()
        
    def calculate_loan_interest_rate(self, credit_score):
        return max(0.01, self.base_interest_rate * (2 - credit_score))
    
    def approve_loan(self, agent, amount):
        if amount > self.money_supply * 0.1:  # Limit loan to 10% of money supply
            return False, 0
        
        interest_rate = self.calculate_loan_interest_rate(agent.credit_score)
        self.total_loans += amount
        self.money_supply -= amount  # Money is lent out, so decrease supply
        agent.loans.append((amount, interest_rate))
        return True, interest_rate

    def lend_to_agents(self):
        for agent in self.model.schedule.agents:
            if isinstance(agent, (Firm, Consumer)) and not agent.bankrupt:
                # Check the attribute for Consumers or Firms based on type
                needed_capital = (agent.initial_capital if isinstance(agent, Firm) else agent.initial_money) * 0.3
                # Update check based on attribute that represents financial status
                if isinstance(agent, Firm):
                    if agent.capital < needed_capital:  # For Firms
                        approved, interest_rate = self.approve_loan(agent, needed_capital)
                        if approved:
                            print(f"Loan approved for Firm ID {agent.unique_id}: Amount = {needed_capital}, Interest Rate = {interest_rate:.2f}")
                elif isinstance(agent, Consumer):
                    if agent.money < needed_capital:  # For Consumers
                        approved, interest_rate = self.approve_loan(agent, needed_capital)
                        if approved:
                            print(f"Loan approved for Consumer ID {agent.unique_id}: Amount = {needed_capital}, Interest Rate = {interest_rate:.2f}")


    def update_inflation_rate(self, current_prices):
        if not current_prices:
            self.inflation_rate = 0
            return
        
        if not self.price_history:
            self.price_history.append(current_prices)
            self.inflation_rate = 0
            return
            
        old_median_price = np.median(self.price_history[-1])
        new_median_price = np.median(current_prices)
        
        if old_median_price > 0:
            self.inflation_rate = ((new_median_price - old_median_price) / old_median_price) * 100
        
        self.price_history.append(current_prices)
        if len(self.price_history) > 12:
            self.price_history.pop(0)
