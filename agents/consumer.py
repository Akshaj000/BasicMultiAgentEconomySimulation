# model.py
from mesa import Agent
import numpy as np
from agents.firm import Firm

class Consumer(Agent):
    def __init__(self, unique_id, model, initial_money, satisfaction_threshold):
        super().__init__(unique_id, model)
        self.money = initial_money
        self.initial_money = initial_money
        self.employer = None
        self.satisfaction = 1.0
        self.loans = []
        self.bankrupt = False
        self.credit_score = 1.0
        self.satisfaction_threshold = satisfaction_threshold
        self.current_firm = None
        self.purchase_history = []
    
    def step(self):
        if not self.bankrupt:
            self.make_purchase_decision()
            self.service_loans()
            self.update_credit_score()
    
    def make_purchase_decision(self):
        firms = [agent for agent in self.model.schedule.agents 
                if isinstance(agent, Firm) and not agent.bankrupt and agent.inventory > 0]
        
        if not firms:
            self.satisfaction *= 0.95  # Decrease satisfaction when no goods available
            return
            
        affordable_firms = [firm for firm in firms if firm.price <= self.money]
        if not affordable_firms:
            self.satisfaction *= 0.9  # Decrease satisfaction when can't afford goods
            return
            
        weights = []
        for firm in affordable_firms:
            price_factor = 1 / (firm.price + 1)
            satisfaction_factor = self.satisfaction if firm == self.current_firm else 0.8
            inventory_factor = min(1, firm.inventory / firm.production_capacity)
            weights.append(price_factor * satisfaction_factor * inventory_factor)
        
        weights = np.array(weights) / sum(weights)
        chosen_firm = np.random.choice(affordable_firms, p=weights)
        self.make_purchase(chosen_firm)
    
    def make_purchase(self, firm):
        if firm.inventory <= 0 or firm.price > self.money:
            self.satisfaction *= 0.9
            return
            
        self.money -= firm.price
        firm.capital += firm.price
        firm.inventory -= 1
        
        # Record purchase for credit score calculation
        self.purchase_history.append(firm.price)
        if len(self.purchase_history) > 12:
            self.purchase_history.pop(0)
        
        # More nuanced satisfaction adjustment
        price_satisfaction = 1 - (firm.price / self.initial_money)
        inventory_satisfaction = min(1, firm.inventory / firm.production_capacity)
        self.satisfaction = 0.8 * self.satisfaction + 0.2 * (price_satisfaction * inventory_satisfaction)
        self.current_firm = firm
    
    def service_loans(self):
        for loan in self.loans[:]:  # Create copy to allow modification during iteration
            amount, rate = loan
            interest_payment = amount * rate
            if interest_payment > self.money:
                self.bankrupt = True
                if self.employer:
                    self.employer.employees.remove(self)
                    self.employer = None
                return
            self.money -= interest_payment
    
    def update_credit_score(self):
        # More sophisticated credit score calculation
        money_ratio = self.money / self.initial_money
        purchase_stability = np.std(self.purchase_history) / np.mean(self.purchase_history) if self.purchase_history else 1
        employment_factor = 1.2 if self.employer else 0.8
        self.credit_score = max(0, min(1, money_ratio * employment_factor * (1 - purchase_stability)))
