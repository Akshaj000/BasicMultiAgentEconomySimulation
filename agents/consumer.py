# consumer.py
from mesa import Agent
from transactions import Transaction
import random

class Consumer(Agent):
    def __init__(self, unique_id, model, initial_money, satisfaction_threshold):
        super().__init__(unique_id, model)
        self.money = initial_money
        self.initial_money = initial_money
        self.satisfaction_threshold = satisfaction_threshold
        self.employer = None
        self.bankrupt = False
        self.loans = []  # Keep track of loans
        self.satisfaction = 1.0  # Satisfaction level (1.0 = fully satisfied)
        self.debt = 0  # Initialize debt

    def step(self):
        """Perform a step for the consumer, including making purchases, updating satisfaction, and servicing loans."""
        if not self.bankrupt:
            self.make_purchase()
            self.update_satisfaction()
            self.service_loans()

    def make_purchase(self):
        """Select a firm to purchase from and execute the transaction."""
        from agents.firm import Firm

        firms = [agent for agent in self.model.schedule.agents if isinstance(agent, Firm) and not agent.bankrupt]
        if not firms:
            return

        firm_to_buy_from = self.employer if self.employer in firms else random.choice(firms)
        purchase_amount = min(self.money, firm_to_buy_from.price)

        if purchase_amount > 0:
            self.money -= purchase_amount
            firm_to_buy_from.capital += purchase_amount
            transaction = Transaction(firm_to_buy_from, self, purchase_amount, 'purchase')
            self.model.add_transaction(transaction)

    def calculate_needed_capital(self):
        """Calculate the amount of capital the consumer needs based on their satisfaction and employment status."""
        average_price = self.model.get_average_price()
        employment_factor = 0.5 if self.employer else 1.5
        satisfaction_factor = 1 - self.satisfaction

        needed_capital = (average_price * 10) * employment_factor * (1 + satisfaction_factor)
        return max(needed_capital, 0)

    def update_satisfaction(self):
        """Adjust the consumer's satisfaction level based on current money and purchase activity."""
        if self.money < self.initial_money * self.satisfaction_threshold:
            self.satisfaction -= 0.1
        else:
            self.satisfaction += 0.05
        self.satisfaction = max(0, min(1, self.satisfaction))

    def get_borrowing_limit(self):
        """Calculate the maximum amount the consumer can borrow based on their financial situation."""
        max_borrowing_factor = 2000.0
        return self.money * max_borrowing_factor

    def service_loans(self):
        """Manage loan requests and repayments based on the consumer's financial condition."""
        basic_expenditure = self.calculate_needed_capital()
        loan_needed = basic_expenditure - self.money * 2

        if loan_needed > 0 and loan_needed <= self.get_borrowing_limit():
            if self.request_loan(loan_needed):
                print(f"Consumer {self.unique_id} requested loan: {loan_needed}")
        else:
            self.handle_existing_loans()

    def handle_existing_loans(self):
        """Process existing loans and attempt to repay interest."""
        for loan in self.loans[:]:
            amount, rate = loan
            interest_payment = amount * rate

            if interest_payment > self.money:
                print(f"Consumer {self.unique_id} unable to pay interest, going bankrupt.")
                self.bankrupt = True
                return
            else:
                self.money -= interest_payment
                self.debt = max(0, self.debt - interest_payment)
                self.model.central_bank.money_supply += interest_payment
                print(f"Consumer {self.unique_id} repaid interest: {interest_payment}")

    def request_loan(self, amount):
        """Request a loan from the central bank, if the amount is within allowable limits."""
        if amount > 0 and amount <= self.get_borrowing_limit():
            approved, interest_rate = self.model.central_bank.approve_loan(self, amount)
            if approved:
                self.money += amount
                self.debt += amount
                self.model.central_bank.money_supply -= amount
                print(f"Loan approved for Consumer {self.unique_id}: Amount={amount}, Rate={interest_rate}")
                self.loans.append((amount, interest_rate))
                return True
        print(f"Loan request denied for Consumer {self.unique_id}: Requested={amount}")
        return False
