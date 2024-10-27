# bank.py
from mesa import Agent
from agents.consumer import Consumer
from transactions import Transaction

class CentralBank(Agent):
    def __init__(self, unique_id, model, initial_money_supply, base_interest_rate):
        super().__init__(unique_id, model)
        self.money_supply = initial_money_supply
        self.base_interest_rate = base_interest_rate
        self.total_loans = 0
        self.bankrupted_firms = 0
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

    def approve_loan(self, agent, needed_capital):
        # Approve loan without considering credit score
        if(self.money_supply > needed_capital):
            return True, self.base_interest_rate
        else:
            return False, 0
        
    def update_inflation_rate(self, firm_prices):
        if firm_prices:
            average_price = sum(firm_prices) / len(firm_prices)
            self.inflation_rate = (average_price / self.money_supply) * 100  # Simple inflation calculation

    def step(self):
        self.lend_to_agents()
