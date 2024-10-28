# bank.py
from mesa import Agent
from agents.consumer import Consumer
from transactions import Transaction
from agents.firm import Firm

class CentralBank(Agent):
    def __init__(self, unique_id, model, initial_money_supply, base_interest_rate):
        super().__init__(unique_id, model)
        self.money_supply = initial_money_supply
        self.base_interest_rate = base_interest_rate
        self.total_loans = 0
        self.bankrupted_firms = 0
        self.previous_avg_price = None
        self.inflation_rate = 0.2
        self.bankrupted_consumers = 0
        self.price_history = []
        
    def step(self):
        self.lend_to_agents()
        
    def calculate_loan_interest_rate(self, credit_score):
        return max(0.01, self.base_interest_rate * (2 - credit_score))
    
    def approve_loan(self, agent, amount):
        if amount > self.money_supply * 0.1:  # Limit loan to 10% of money supply
            return False, 0
        
        interest_rate = self.calculate_loan_interest_rate(agent.credit_score)
        self.total_loans += amount
        self.money_supply -= amount  # Money is lent out, so decrease supply
        agent.loans.append((amount, interest_rate))
        return True, interest_rate

    def lend_to_agents(self):
        for agent in self.model.schedule.agents:
            if isinstance(agent, Consumer) and not agent.bankrupt:
                needed_capital = agent.calculate_needed_capital()
                approved, interest_rate = self.approve_loan(agent, needed_capital)

                if approved:
                    loan_amount = needed_capital
                    agent.money += loan_amount
                    self.money_supply -= loan_amount
                    self.total_loans += loan_amount
                    agent.debt += loan_amount  # Ensure you have a debt attribute in Consumer class
                    print(f"Lent {loan_amount} to Consumer {agent.unique_id}. Total debt now: {agent.debt}")
            elif isinstance(agent,Firm) and not agent.bankrupt:
                needed_capital = agent.initial_capital * 0.2  # Firm can borrow up to 10% of initial capital
                approved, interest_rate = self.approve_loan(agent, needed_capital)

                if approved:
                    loan_amount = needed_capital
                    agent.capital += loan_amount
                    self.money_supply -= loan_amount
                    self.total_loans += loan_amount
                    print(f"Lent {loan_amount} to Firm {agent.unique_id}.")

    def approve_loan(self, agent, needed_capital):
        # Approve loan without considering credit score
        if(self.money_supply > needed_capital):
            return True, self.base_interest_rate
        else:
            return False, 0
        
    # In CentralBank class
    def update_inflation_rate(self, prices):
        if len(prices) > 0:
            current_avg_price = sum(prices) / len(prices)
            if self.previous_avg_price is not None:
                self.inflation_rate = (current_avg_price - self.previous_avg_price) / self.previous_avg_price
            self.previous_avg_price = current_avg_price
        else:
            self.inflation_rate = 0


    def step(self):
        self.lend_to_agents()
