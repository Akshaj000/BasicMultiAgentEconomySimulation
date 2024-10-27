# consumer.py
from mesa import Agent
from transactions import Transaction

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
        if not self.bankrupt:
            self.make_purchase()
            self.update_satisfaction()
            self.service_loans()

    def make_purchase(self):
        # Simulate making a purchase
        if self.employer:
            purchase_amount = min(self.money, self.employer.price)
            if purchase_amount > 0:
                self.money -= purchase_amount
                transaction = Transaction(self.employer, self, purchase_amount, 'purchase')
                self.model.add_transaction(transaction)

    def calculate_needed_capital(self):
        # Get the average price of goods from the model
        average_price = self.model.get_average_price()
        
        # Determine if the consumer is employed and their current satisfaction level
        employment_factor = 0.5 if self.employer else 1.5  # Employed consumers need less capital
        satisfaction_factor = 1 - self.satisfaction  # Dissatisfied consumers need more capital
        
        # Calculate needed capital based on average price, employment status, and satisfaction
        needed_capital = (average_price * 10) * employment_factor * (1 + satisfaction_factor)  # Example calculation
        return max(needed_capital, 0)  # Ensure it's not negative

    def update_satisfaction(self):
        # Satisfaction decreases if money is low or if no purchases were made
        if self.money < self.initial_money * self.satisfaction_threshold:
            self.satisfaction -= 0.1  # Decrease satisfaction
        else:
            self.satisfaction += 0.05  # Increase satisfaction
        self.satisfaction = max(0, min(1, self.satisfaction))  # Keep it within bounds

    def get_borrowing_limit(self):
        # Define a borrowing limit based on current money and satisfaction level.
        max_borrowing_factor = 2.0  # Example factor
        return (self.money * max_borrowing_factor) - self.debt  # Return remaining borrowing capacity
    
    def service_loans(self):
        # Check if the consumer can pay for basic expenditures first
        basic_expenditure = self.calculate_needed_capital()  # Use your existing method to determine needed capital for expenses
        
        if self.money < basic_expenditure:
            # Request a loan if they can't cover basic expenditures
            loan_needed = basic_expenditure - self.money
            if loan_needed > self.get_borrowing_limit():  # Check if the loan needed is within borrowing limit
                loan_needed = self.get_borrowing_limit()  # Cap it at borrowing limit
            if self.request_loan(loan_needed):  # Attempt to request the loan
                print(f"Consumer {self.unique_id} requested loan: {loan_needed}")
        else:
            # If they can cover expenditures, handle existing loans
            for loan in self.loans[:]:
                amount, rate = loan
                interest_payment = amount * rate

                if interest_payment > self.money:  # Check if they can pay interest
                    print(f"Consumer {self.unique_id} unable to pay interest, going bankrupt.")
                    self.bankrupt = True
                    return
                else:
                    self.money -= interest_payment  # Pay the interest
                    self.debt = max(0,self.debt-interest_payment)  # Decrease debt
                    self.model.central_bank.money_supply += interest_payment  # Add payment back to bank's supply
                    print(f"Consumer {self.unique_id} repaid interest: {interest_payment}")

    def request_loan(self, amount):
        # Ensure the loan request is reasonable and the bank has enough funds
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
