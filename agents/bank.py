from mesa import Agent
from agents.firm import Firm
from agents.consumer import Consumer
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
        self.wealth_threshold = 100000  # Adjust this threshold as needed

    def step(self):
        self.lend_to_agents()
        self.update_inflation_rate(self.price_history)  # Update inflation based on price history

    def calculate_loan_interest_rate(self, agent):
        # Dynamic interest rate based on inflation
        inflation_adjustment = self.inflation_rate * 2  # Adjust the multiplier as needed
        base_rate = self.base_interest_rate + inflation_adjustment

        if isinstance(agent, Firm):
            if agent.capital > self.wealth_threshold:
                return base_rate - 0.02  # Slightly lower for wealthier firms
            return base_rate  # Higher for those with lower capital
        else:
            # Consumers always get the adjusted base rate
            return base_rate

    def approve_loan(self, agent, amount):
        if isinstance(agent, Firm):
            # Cap the loan amount for firms based on their capital
            max_loan_amount = agent.capital * 0.5  # Example: allow loans up to 50% of their current capital
            amount = min(amount, max_loan_amount)  # Ensure they don't exceed this limit

            interest_rate = self.calculate_loan_interest_rate(agent)
            self.total_loans += amount
            self.money_supply -= amount
            agent.loans.append((amount, interest_rate))
            return True, interest_rate
        else:
            # Consumers must meet money supply restrictions
            if amount > self.money_supply * 0.1:  # 10% limit for consumers
                return False, 0
            interest_rate = self.calculate_loan_interest_rate(agent)
            self.total_loans += amount
            self.money_supply -= amount
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
                    agent.debt += loan_amount  # Assume a debt attribute exists in Consumer
                    print(f"Lent {loan_amount} to Consumer {agent.unique_id}. Total debt now: {agent.debt}")

            elif isinstance(agent, Firm) and not agent.bankrupt:
                needed_capital = agent.calculate_needed_capital()
                approved, interest_rate = self.approve_loan(agent, needed_capital)

                if approved:
                    loan_amount = needed_capital
                    agent.capital += loan_amount
                    print(f"Lent {loan_amount} to Firm {agent.unique_id}.")

    def update_inflation_rate(self, prices):
        # Update inflation rate based on price history
        if prices:
            current_avg_price = sum(prices) / len(prices)
            if self.previous_avg_price is not None:
                self.inflation_rate = (current_avg_price - self.previous_avg_price) / self.previous_avg_price
            self.previous_avg_price = current_avg_price
        else:
            self.inflation_rate = 0
