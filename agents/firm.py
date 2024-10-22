import mesa
import random

class Firm(mesa.Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.money = 2000
        self.debt = 0
        self.interest_rate = 0
        self.productivity = random.uniform(0.8, 1.2)
        self.inventory = 100
        self.price = 10

    def borrow(self, amount, rate):
        self.money += amount
        self.debt += amount
        self.interest_rate = rate

    def produce(self):
        production_cost = self.money * 0.3
        if self.money >= production_cost:
            self.money -= production_cost
            self.inventory += int(production_cost * self.productivity)

    def sell(self):
        sales = min(self.inventory, random.randint(50, 150))
        revenue = sales * self.price * (1 + self.model.central_bank.inflation_rate)
        self.money += revenue
        self.inventory -= sales
        return revenue

    def pay_debt(self):
        interest_payment = self.debt * self.interest_rate
        principal_payment = min(self.money * 0.2, self.debt)
        if self.money >= (interest_payment + principal_payment):
            self.money -= (interest_payment + principal_payment)
            self.debt -= principal_payment

    def step(self):
        self.produce()
        self.sell()
        self.pay_debt()
