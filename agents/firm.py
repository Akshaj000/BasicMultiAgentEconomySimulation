from mesa import Agent
import numpy as np

class Firm(Agent):
    def __init__(self, unique_id, model, initial_capital, initial_inventory, base_price):
        super().__init__(unique_id, model)
        self.capital = initial_capital
        self.inventory = initial_inventory
        self.price = base_price
        self.employees = []
        self.base_salary = 1000  # Base monthly salary per employee
        self.profit = 0
        self.valuation = initial_capital
        self.loan_payment = 0
        self.production_rate = 100  # Base production per employee
        
    def hire_employee(self, consumer):
        """Hire a consumer if the firm can afford it"""
        if consumer not in self.employees:
            self.employees.append(consumer)
            consumer.employer = self
            consumer.salary = self.base_salary
            return True
        return False
        
    def layoff_employee(self, consumer):
        """Lay off an employee if necessary"""
        if consumer in self.employees:
            self.employees.remove(consumer)
            consumer.employer = None
            consumer.salary = 0
            return True
        return False
        
    def adjust_prices(self):
        """Adjust prices based on supply and demand with more volatility"""
        total_demand = sum([c.money for c in self.model.get_consumers()]) / self.price
        supply = self.inventory
        
        # Price adjustment factor based on supply-demand ratio
        adjustment_factor = (total_demand - supply) / max(supply, 1)
        
        # Add market sentiment (random factor)
        market_sentiment = self.model.random.uniform(-0.05, 0.05)
        
        # Consider inflation expectations
        inflation_expectation = max(self.model.central_bank.inflation_rate, 0) / 100
        
        # Combine all factors
        total_adjustment = (adjustment_factor * 0.3 + 
                        market_sentiment +
                        inflation_expectation)
        
        # Apply the price change with constraints
        max_adjustment = 0.2  # Maximum 20% price change per step
        adjustment = np.clip(total_adjustment, -max_adjustment, max_adjustment)
        self.price *= (1 + adjustment)
        
        # Ensure minimum price
        self.price = max(self.price, 1.0)
        
    def produce_goods(self):
        """Produce new inventory based on number of employees"""
        production = len(self.employees) * self.production_rate
        self.inventory += production
        
    def pay_salaries(self):
        """Pay salaries to all employees"""
        total_salaries = sum(employee.salary for employee in self.employees)
        
        if total_salaries > self.capital:
            # Need to reduce workforce or salaries
            while total_salaries > self.capital and self.employees:
                laid_off = self.employees[-1]
                self.layoff_employee(laid_off)
                total_salaries = sum(employee.salary for employee in self.employees)
        
        self.capital -= total_salaries
        for employee in self.employees:
            employee.receive_salary(employee.salary)
            
    def adjust_salaries(self):
        """Adjust salaries based on profitability"""
        if self.profit > len(self.employees) * self.base_salary * 2:  # Very profitable
            for employee in self.employees:
                employee.salary *= 1.1  # 10% raise
        elif self.profit < 0:  # Losing money
            for employee in self.employees:
                employee.salary *= 0.9  # 10% reduction
                
    def pay_loan(self, amount):
        """Pay loan to central bank"""
        if self.capital >= amount:
            self.capital -= amount
            return True
        return False
        
    def sell_goods(self, quantity, buyer):
        """Sell goods to a consumer"""
        if quantity <= self.inventory:
            revenue = quantity * self.price
            self.inventory -= quantity
            self.capital += revenue
            return True
        return False
        
    def calculate_profit(self):
        """Calculate monthly profit"""
        total_salaries = sum(employee.salary for employee in self.employees)
        revenue = self.price * (self.production_rate * len(self.employees) - self.inventory)
        self.profit = revenue - total_salaries - self.loan_payment
        self.valuation += self.profit
        
    def step(self):
        """Monthly actions of the firm"""
        self.produce_goods()
        self.adjust_prices()
        self.pay_salaries()
        self.calculate_profit()
        self.adjust_salaries()

    # Update the adjust_prices method in the Firm class

