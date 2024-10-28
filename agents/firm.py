from mesa import Agent
import numpy as np
from transactions import Transaction
from agents.consumer import Consumer

class Firm(Agent):
    def __init__(self, unique_id, model, initial_capital, market_volatility):
        super().__init__(unique_id, model)
        self.capital = initial_capital
        self.initial_capital = initial_capital
        self.price = max(1, initial_capital * 0.001)
        self.production_capacity = max(1, int(initial_capital / 1000))
        self.inventory = 0
        self.employees = []
        self.loans = []
        self.market_volatility = market_volatility
        self.bankrupt = False
        self.wage = 2000  # Initial wage
        self.costs_history = []
        self.inventory_threshold = 5  # Set a threshold for low inventory
        self.profit_margin = 0.1  # Margin added to cover costs and control pricing inflation

    def step(self):
        if not self.bankrupt:
            if self.inventory < self.inventory_threshold:
                self.produce()
            self.adjust_wages()
            self.pay_wages()
            self.adjust_price()
            self.service_loans()
            self.invest()

    def adjust_wages(self):
        inflation_rate = self.model.central_bank.inflation_rate
        self.wage = max(0, self.wage * (1 + inflation_rate * 0.5))  # Scale inflation effect to control excess
        print(f"Firm {self.unique_id} adjusted wage to {self.wage}")

    def adjust_price(self):
        active_consumers = [agent for agent in self.model.schedule.agents if isinstance(agent, Consumer) and not agent.bankrupt]
        avg_consumer_money = sum(consumer.money for consumer in active_consumers) / len(active_consumers) if active_consumers else 0

        production_cost_per_unit = (self.wage * len(self.employees) + self.production_capacity * 20) / max(1, self.production_capacity)
        minimum_price = production_cost_per_unit * (1 + self.profit_margin)

        inventory_factor = max(0.9, min(1.1, 1 - (self.inventory / (self.production_capacity * 2))))
        demand_factor = min(1.05, 1 + (avg_consumer_money - self.model.central_bank.base_interest_rate) / 20000)
        volatility_factor = 1 + (np.random.random() - 0.5) * self.market_volatility * 0.05

        adjusted_price = self.price * inventory_factor * demand_factor * volatility_factor
        self.price = max(minimum_price, adjusted_price)
        print(f"Firm {self.unique_id} adjusted price to {self.price}, minimum needed: {minimum_price}")

    def produce(self):
        labor_cost = sum(self.wage for _ in self.employees)
        material_cost = self.production_capacity * 20
        total_cost = labor_cost + material_cost

        if self.capital < total_cost * 1.5:
            loan_amount = max(total_cost * 0.5, 1000)  # Cap loan amount to 50% of total cost
            if not self.request_loan(loan_amount):
                print(f"Firm {self.unique_id} failed to secure a loan before bankruptcy.")
                self.bankrupt = True
                return

        if total_cost > self.capital:
            self.production_capacity = max(1, int(self.capital / (labor_cost + 50)))
            total_cost = self.production_capacity * 50 + labor_cost

        if total_cost <= self.capital:
            self.capital -= total_cost
            self.inventory += self.production_capacity
            self.costs_history.append(total_cost)
            print(f"Firm {self.unique_id} produced {self.production_capacity} units at cost {total_cost}")
        else:
            print(f"Firm {self.unique_id} cannot afford to produce due to insufficient capital. Inventory: {self.inventory}, Capital: {self.capital}")
    
    def calculate_needed_capital(self):
        total_wages = self.wage * len(self.employees)
        total_loan_payments = sum(amount * rate for amount, rate in self.loans)
        production_cost_per_step = (self.production_capacity * 20) + (self.wage * len(self.employees))
        total_production_cost = production_cost_per_step

        needed_capital = total_wages + total_loan_payments + total_production_cost
        print(f"Firm {self.unique_id} needs {needed_capital} to survive.")
        return needed_capital

    def pay_wages(self):
        total_wages = sum(self.wage for _ in self.employees)
        while total_wages > self.capital and self.employees:
            self.lay_off_employees()
            total_wages = sum(self.wage for _ in self.employees)

        if total_wages > self.capital:
            loan_amount = max(total_wages * 0.5, 1000)  # Cap loan to 50% of wages
            if not self.request_loan(loan_amount):
                print(f"Firm {self.unique_id} failed to secure a loan before bankruptcy.")
                self.bankrupt = True
                return
            return

        for employee in self.employees:
            self.capital -= self.wage
            employee.money += self.wage
            transaction = Transaction(self, employee, self.wage, 'wage')
            self.model.add_transaction(transaction)
            print(f"Firm {self.unique_id} paid {self.wage} to Consumer {employee.unique_id}")
            print(f"Firm {self.unique_id} capital: {self.capital}")
            print(f"Consumer {employee.unique_id} money: {employee.money}")

    def service_loans(self):
        for loan in self.loans[:]:
            amount, rate = loan
            interest_payment = amount * rate
            if interest_payment > self.capital:
                self.lay_off_employees()
                if self.capital < interest_payment:
                    self.bankrupt = True
                    print(f"Firm {self.unique_id} went bankrupt due to loan payment failure.")
                    return
            self.capital -= interest_payment
            self.model.central_bank.money_supply += interest_payment
            print(f"Firm {self.unique_id} paid {interest_payment} in loan interest.")

    def request_loan(self, amount):
        if self.model.central_bank.money_supply >= amount:
            self.loans.append((amount, self.model.central_bank.base_interest_rate))
            self.capital += amount
            self.model.central_bank.money_supply -= amount
            print(f"Firm {self.unique_id} received loan: {amount}")
            return True
        print(f"Firm {self.unique_id} failed to request loan: insufficient bank funds.")
        return False

    def lay_off_employees(self):
        if self.employees:
            employee_to_lay_off = self.employees.pop()
            employee_to_lay_off.employer = None
            print(f"Firm {self.unique_id} laid off an employee.")

    def invest(self):
        if self.capital > 500 + self.wage * len(self.employees):
            investment_amount = min(0.1 * self.capital, 500)
            self.capital -= investment_amount
            self.production_capacity += investment_amount // 200
            print(f"Firm {self.unique_id} invested {investment_amount} to increase capacity to {self.production_capacity}")
