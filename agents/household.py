import mesa
import random

class Household(mesa.Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.money = 1000
        self.debt = 0
        self.interest_rate = 0
        self.happiness = 100
        self.income = random.uniform(50, 150)

    def borrow(self, amount, rate):
        self.money += amount
        self.debt += amount
        self.interest_rate = rate

    def earn_income(self):
        self.money += self.income

    def meet_consumption_needs(self):
        desired_spending = self.money * random.uniform(0.1, 0.3)
        actual_spending = min(desired_spending, self.money)
        self.money -= actual_spending
        self.happiness = min(100, self.happiness + actual_spending/100)
        return actual_spending

    def pay_debt(self):
        interest_payment = self.debt * self.interest_rate
        principal_payment = min(self.money * 0.2, self.debt)
        if self.money >= (interest_payment + principal_payment):
            self.money -= (interest_payment + principal_payment)
            self.debt -= principal_payment
        else:
            self.happiness -= 10

    def step(self):
        self.earn_income()
        self.meet_consumption_needs()
        self.pay_debt()
        self.happiness = max(0, self.happiness - 5)
