# firm.py
from mesa import Agent
import numpy as np
from transactions import Transaction

class Firm(Agent):
    def __init__(self, unique_id, model, initial_capital, market_volatility):
        super().__init__(unique_id, model)
        self.capital = initial_capital
        self.initial_capital = initial_capital
        self.price = max(1, initial_capital * 0.1)  # Ensure positive price
        self.production_capacity = max(1, int(initial_capital / 1000))
        self.inventory = 0
        self.employees = []
        self.loans = []
        self.market_volatility = market_volatility
        self.bankrupt = False
        self.credit_score = 1.0
        self.wage = 100
        self.costs_history = []
        
    def step(self):
        if not self.bankrupt:
            self.adjust_price()
            self.produce()
            self.pay_wages()
            self.service_loans()
            self.update_credit_score()
    
    def adjust_price(self):
        # Dynamic price adjustment based on inventory and market conditions
        inventory_factor = max(0.8, min(1.2, 1 - (self.inventory / (self.production_capacity * 2))))
        volatility_factor = 1 + (np.random.random() - 0.5) * self.market_volatility
        self.price = max(1, self.price * inventory_factor * volatility_factor)
    
    def produce(self):
        labor_cost = sum(self.wage for _ in self.employees)
        material_cost = self.production_capacity * 50
        total_cost = labor_cost + material_cost
        
        if total_cost > self.capital:
            self.production_capacity = max(1, int(self.capital / (labor_cost + 50)))
            total_cost = self.production_capacity * 50 + labor_cost
            
        self.capital -= total_cost
        self.inventory += self.production_capacity
        self.costs_history.append(total_cost)
        if len(self.costs_history) > 12:
            self.costs_history.pop(0)
    
    def pay_wages(self):
        total_wages = sum(self.wage for _ in self.employees)
        if total_wages > self.capital:
            self.bankrupt = True
            for employee in self.employees:
                employee.employer = None
            self.employees.clear()
            return
            
        for employee in self.employees:
            self.capital -= self.wage
            employee.money += self.wage
            transaction = Transaction(self, employee, self.wage, 'wage')
            self.model.add_transaction(transaction)
    
    def service_loans(self):
        for loan in self.loans[:]:  # Create copy to allow modification during iteration
            amount, rate = loan
            interest_payment = amount * rate
            if interest_payment > self.capital:
                self.bankrupt = True
                return
            self.capital -= interest_payment
    
    def update_credit_score(self):
        # More sophisticated credit score calculation
        capital_ratio = self.capital / self.initial_capital
        cost_stability = np.std(self.costs_history) / np.mean(self.costs_history) if self.costs_history else 1
        self.credit_score = max(0, min(1, capital_ratio * (1 - cost_stability)))
