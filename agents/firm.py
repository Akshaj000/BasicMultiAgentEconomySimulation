# firm.py
from mesa import Agent
import numpy as np
from transactions import Transaction

class Firm(Agent):
    def __init__(self, unique_id, model, initial_capital, market_volatility):
        super().__init__(unique_id, model)
        self.capital = initial_capital
        self.initial_capital = initial_capital
        self.price = max(1, initial_capital * 0.01)
        self.production_capacity = max(1, int(initial_capital / 1000))
        self.inventory = 0
        self.employees = []
        self.loans = []
        self.market_volatility = market_volatility
        self.bankrupt = False
        self.wage = 2000
        self.costs_history = []

    def step(self):
        if not self.bankrupt:
            self.adjust_price()
            self.produce()
            self.pay_wages()
            self.service_loans()
            self.invest()  # Attempt to invest to increase capital

    def adjust_price(self):
        inventory_factor = max(0.8, min(1.2, 1 - (self.inventory / (self.production_capacity * 2))))
        volatility_factor = 1 + (np.random.random() - 0.5) * self.market_volatility
        self.price = max(1, self.price * inventory_factor * volatility_factor)

    def produce(self):
        labor_cost = sum(self.wage for _ in self.employees)
        material_cost = self.production_capacity * 20
        total_cost = labor_cost + material_cost
        
        if total_cost > self.capital:
            # If unable to pay costs, reduce production capacity
            self.production_capacity = max(1, int(self.capital / (labor_cost + 50)))
            total_cost = self.production_capacity * 50 + labor_cost
            
        self.capital -= total_cost
        self.inventory += self.production_capacity
        self.costs_history.append(total_cost)

    def pay_wages(self):
        total_wages = sum(self.wage for _ in self.employees)
        
        # If total wages exceed capital, try to borrow or lay off employees
        while total_wages > self.capital:
            if self.request_loan(min(total_wages - self.capital, 500)):  # Request a loan to cover wages
                total_wages = sum(self.wage for _ in self.employees)  # Recalculate after loan
            else:
                self.lay_off_employees()
                total_wages = sum(self.wage for _ in self.employees)  # Recalculate after layoffs
        
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
        for loan in self.loans[:]:
            amount, rate = loan
            interest_payment = amount * rate
            if interest_payment > self.capital:
                self.bankrupt = True
                return
            self.capital -= interest_payment
            self.model.central_bank.money_supply += interest_payment

    def request_loan(self, amount):

        if self.model.central_bank.money_supply > amount:  # Ensure bank has enough money
            self.loans.append((amount, self.model.central_bank.base_interest_rate))  # Simple loan request
            self.capital += amount
            self.model.central_bank.money_supply -= amount  # Deduct from bank supply
            print(f"Firm {self.unique_id} received loan: {amount}")
            return True
        return False

    def lay_off_employees(self):
        # Lay off employees if unable to pay wages
        if self.employees:
            employee_to_lay_off = self.employees.pop()  # Lay off the last employee
            employee_to_lay_off.employer = None

    def invest(self):
        if self.capital > 200:  # Check if there is enough capital to invest
            investment_amount = 200  # Example fixed investment amount
            self.capital -= investment_amount
            self.production_capacity += investment_amount // 1000  # Increase capacity based on investment
