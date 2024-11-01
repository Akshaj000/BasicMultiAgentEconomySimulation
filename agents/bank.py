# bank.py
from mesa import Agent
from agents.firm import Firm
from agents.consumer import Consumer
from transactions import Transaction

class CentralBank(Agent):
    def __init__(self, unique_id, model, initial_money_supply, base_interest_rate,toggle):
        super().__init__(unique_id, model)
        self.money_supply = initial_money_supply
        self.base_interest_rate = base_interest_rate
        self.total_loans = 0
        self.bankrupted_firms = 0
        self.previous_avg_price = None
        self.inflation_rate = 0.2
        self.bankrupted_consumers = 0
        self.price_history = []
        self.wealth_threshold = 100000 

    def step(self):
        """Lend to agents and update the inflation rate based on price history."""
        self.lend_to_agents()
        self.update_inflation_rate(self.price_history)

    def calculate_loan_interest_rate(self, agent):
        """Calculate the loan interest rate based on the agent's type and current inflation rate."""
        inflation_adjustment = self.inflation_rate * 2
        base_rate = self.base_interest_rate + inflation_adjustment

        if isinstance(agent, Firm):
            return base_rate - 0.02 if agent.capital > self.wealth_threshold else base_rate
        return base_rate

    def approve_loan(self, agent, amount):
        """Approve a loan for the agent based on their type and current capital."""
        max_loan_amount = self.get_max_loan_amount(agent, amount)
        if max_loan_amount is None:
            return False, 0

        interest_rate = self.calculate_loan_interest_rate(agent)
        self.record_loan(agent, max_loan_amount, interest_rate)
        return True, interest_rate

    def get_max_loan_amount(self, agent, amount):
        """Calculate the maximum loan amount based on agent type and capital."""
        if isinstance(agent, Firm):
            return min(amount, agent.capital * 0.5)
        if amount <= self.money_supply * 0.1:  # 10% limit for consumers
            return amount
        return None

    def record_loan(self, agent, amount, interest_rate):
        """Record the loan transaction and update the agent's financials."""
        self.total_loans += amount
        self.money_supply -= amount
        agent.loans.append((amount, interest_rate))
        transaction = Transaction(self, agent, amount, "loan")
        self.model.add_transaction(transaction)

    def lend_to_agents(self):
        """Lend to consumers and firms that are not bankrupt and need capital."""
        for agent in self.model.schedule.agents:
            if isinstance(agent, (Consumer, Firm)) and not agent.bankrupt:
                needed_capital = agent.calculate_needed_capital()
                approved, _ = self.approve_loan(agent, needed_capital)
                
                if approved:
                    self.process_loan(agent, needed_capital)


    def process_loan(self, agent, loan_amount):
        """Process the loan for the agent and update their financials."""
        if isinstance(agent, Consumer):
            agent.money += loan_amount
            agent.debt += loan_amount
            print(f"Lent {loan_amount} to Consumer {agent.unique_id}. Total debt now: {agent.debt}")
        elif isinstance(agent, Firm):
            agent.capital += loan_amount
            print(f"Lent {loan_amount} to Firm {agent.unique_id}.")

    def update_inflation_rate(self, prices):
        """Update the inflation rate based on historical price data."""
        if prices:
            current_avg_price = sum(prices) / len(prices)
            if self.previous_avg_price is not None:
                self.inflation_rate = (current_avg_price - self.previous_avg_price) / self.previous_avg_price
            self.previous_avg_price = current_avg_price
        else:
            self.inflation_rate = 0

