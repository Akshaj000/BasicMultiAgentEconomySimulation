# bank.py
from mesa import Agent
import numpy as np

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
        
    def calculate_loan_interest_rate(self, credit_score):
        # Add minimum interest rate to prevent negative rates
        return max(0.01, self.base_interest_rate * (2 - credit_score))
    
    def approve_loan(self, amount, credit_score):
        # Add stricter loan approval criteria
        if (credit_score < 0.3 or 
            amount > self.money_supply * 0.1 or 
            self.total_loans > self.money_supply * 0.5):
            return False, 0
        interest_rate = self.calculate_loan_interest_rate(credit_score)
        self.total_loans += amount
        self.money_supply += amount
        return True, interest_rate
    
    def update_inflation_rate(self, current_prices):
        if not current_prices:
            self.inflation_rate = 0
            return
        
        if not self.price_history:
            self.price_history.append(current_prices)
            self.inflation_rate = 0
            return
            
        # Use median instead of mean for more stable inflation calculation
        old_median_price = np.median(self.price_history[-1])
        new_median_price = np.median(current_prices)
        
        if old_median_price > 0:
            self.inflation_rate = ((new_median_price - old_median_price) / old_median_price) * 100
        
        self.price_history.append(current_prices)
        if len(self.price_history) > 12:
            self.price_history.pop(0)

