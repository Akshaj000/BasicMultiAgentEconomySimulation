from mesa import Agent
import numpy as np

class Consumer(Agent):
    def __init__(self, unique_id, model, initial_money):
        super().__init__(unique_id, model)
        self.money = initial_money
        self.salary = 0
        self.employer = None
        self.loan_payment = 0
        self.satisfaction = 100  # Scale of 0-100
        self.monthly_needs = 500  # Minimum monthly consumption needed
        
    def receive_salary(self, amount):
        """Receive monthly salary"""
        self.money += amount
        
    def pay_loan(self, amount):
        """Pay monthly loan payment"""
        if self.money >= amount:
            self.money -= amount
            self.loan_payment = amount
            return True
        return False
        
    def request_loan(self, amount, term_months):
        """Request a loan from the central bank"""
        central_bank = self.model.get_central_bank()
        if self.salary > 0:  # Must be employed to get a loan
            max_affordable_payment = self.salary * 0.3  # 30% of salary
            loan_amount, monthly_payment = central_bank.grant_loan(self, amount, term_months)
            
            if monthly_payment <= max_affordable_payment:
                self.money += loan_amount
                self.loan_payment = monthly_payment
                return True
        return False
        
    def buy_goods(self):
        """Buy goods from firms"""
        firms = self.model.get_firms()
        if not firms:
            return
            
        # Try to buy needed goods
        money_for_goods = min(self.money, self.monthly_needs * 1.5)  # Will spend up to 150% of needs if has money
        
        # Find cheapest firm
        firms_with_inventory = [f for f in firms if f.inventory > 0]
        if not firms_with_inventory:
            return
            
        chosen_firm = min(firms_with_inventory, key=lambda x: x.price)
        quantity = money_for_goods / chosen_firm.price
        
        if chosen_firm.sell_goods(quantity, self):
            self.money -= quantity * chosen_firm.price
            
    def calculate_satisfaction(self):
        """Calculate satisfaction based on financial situation"""
        # Factors affecting satisfaction:
        # 1. Having a job
        # 2. Money after expenses
        # 3. Ability to meet monthly needs
        
        base_satisfaction = 50  # Base satisfaction level
        
        # Employment factor (±30 points)
        employment_factor = 30 if self.employer else -30
        
        # Financial factor (±20 points)
        money_after_expenses = self.money - self.monthly_needs - self.loan_payment
        financial_factor = np.clip(money_after_expenses / self.monthly_needs * 20, -20, 20)
        
        self.satisfaction = np.clip(base_satisfaction + employment_factor + financial_factor, 0, 100)
        
    def step(self):
        """Monthly actions of the consumer"""
        self.buy_goods()
        self.calculate_satisfaction()