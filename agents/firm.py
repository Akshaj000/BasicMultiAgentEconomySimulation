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

    def step(self):
        if not self.bankrupt:
            self.adjust_wages()  # Adjust wages based on inflation
            self.adjust_price()
            self.produce()
            self.pay_wages()
            self.service_loans()
            self.invest()  # Invest to increase production capacity

    def adjust_wages(self):
        inflation_rate = self.model.central_bank.inflation_rate
        self.wage = max(0, self.wage * (1 + inflation_rate))
        print(f"Firm {self.unique_id} adjusted wage to {self.wage}")

    def adjust_price(self):
        active_consumers = [agent for agent in self.model.schedule.agents if isinstance(agent, Consumer) and not agent.bankrupt]
        avg_consumer_money = sum(consumer.money for consumer in active_consumers) / len(active_consumers) if active_consumers else 0

        inventory_factor = max(0.8, min(1.2, 1 - (self.inventory / (self.production_capacity * 2))))
        demand_factor = 1 + (avg_consumer_money - self.model.central_bank.base_interest_rate) / 10000
        volatility_factor = 1 + (np.random.random() - 0.5) * self.market_volatility

        self.price = max(1, self.price * inventory_factor * demand_factor * volatility_factor)
        print(f"Firm {self.unique_id} adjusted price to {self.price}")

    def produce(self):
        labor_cost = sum(self.wage for _ in self.employees)
        material_cost = self.production_capacity * 20
        total_cost = labor_cost + material_cost

        # Check if production costs are greater than available capital, and reduce capacity if needed
        if total_cost > self.capital:
            self.production_capacity = max(1, int(self.capital / (labor_cost + 50)))
            total_cost = self.production_capacity * 50 + labor_cost

        if total_cost <= self.capital:
            self.capital -= total_cost
            self.inventory += self.production_capacity
            self.costs_history.append(total_cost)
            print(f"Firm {self.unique_id} produced {self.production_capacity} units at cost {total_cost}")
        else:
            print(f"Firm {self.unique_id} cannot afford to produce due to insufficient capital.")
        print(f"Firm {self.unique_id} inventory: {self.inventory}")
        print(f"Firm {self.unique_id} capital: {self.capital}")

    def pay_wages(self):
        total_wages = sum(self.wage for _ in self.employees)
        
        # Reduce employee count if wages exceed capital
        while total_wages > self.capital and self.employees:
            self.lay_off_employees()
            total_wages = sum(self.wage for _ in self.employees)
        
        if total_wages > self.capital:
            # Declare bankruptcy if wages cannot be paid
            self.bankrupt = True
            for employee in self.employees:
                employee.employer = None
            self.employees.clear()
            print(f"Firm {self.unique_id} went bankrupt due to wage costs.")
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
                # Lay off employees if loan payments cannot be met
                self.lay_off_employees()
                if self.capital < interest_payment:
                    self.bankrupt = True
                    print(f"Firm {self.unique_id} went bankrupt due to loan payment failure.")
                    return
            self.capital -= interest_payment
            self.model.central_bank.money_supply += interest_payment

    def request_loan(self, amount):
        if self.model.central_bank.money_supply > amount:
            self.loans.append((amount, self.model.central_bank.base_interest_rate))
            self.capital += amount
            self.model.central_bank.money_supply -= amount
            print(f"Firm {self.unique_id} received loan: {amount}")
            return True
        return False

    def lay_off_employees(self):
        if self.employees:
            employee_to_lay_off = self.employees.pop()
            employee_to_lay_off.employer = None
            print(f"Firm {self.unique_id} laid off an employee.")

    def invest(self):
        # Adjust investment to ensure sustainability
        if self.capital > 500 + self.wage * len(self.employees):
            investment_amount = min(0.1 * self.capital, 500)
            self.capital -= investment_amount
            self.production_capacity += investment_amount // 200
            print(f"Firm {self.unique_id} invested {investment_amount} to increase capacity to {self.production_capacity}")
