from mesa import Agent
import numpy as np
from agents.consumer import Consumer  # Update this import

class CentralBank(Agent):
    def __init__(self, unique_id, model, initial_money_supply, base_interest_rate):
        super().__init__(unique_id, model)
        self.money_supply = initial_money_supply
        self.base_interest_rate = base_interest_rate
        self.total_loans = 0
        self.bankrupted_firms = 0
        self.bankrupted_consumers = 0
        self.inflation_rate = 0
        self.loan_registry = {}  # {agent_id: (principal, interest, remaining_payments)}
        
    def grant_loan(self, agent, amount, term_months):
        """Grant a loan to an agent if they qualify"""
        if self.money_supply >= amount:
            monthly_interest = self.base_interest_rate / 12
            monthly_payment = (amount * monthly_interest * (1 + monthly_interest)**term_months) / ((1 + monthly_interest)**term_months - 1)
            
            self.loan_registry[agent.unique_id] = {
                'principal': amount,
                'monthly_payment': monthly_payment,
                'remaining_payments': term_months,
                'original_term': term_months
            }
            
            self.money_supply -= amount
            self.total_loans += amount
            return amount, monthly_payment
        return 0, 0

    def collect_payments(self):
        """Collect monthly payments from all borrowers"""
        defaulted_agents = []
        
        for agent_id, loan_info in self.loan_registry.items():
            agent = self.model.schedule.agents_by_id.get(agent_id)
            if agent is None:
                continue
                
            if agent.pay_loan(loan_info['monthly_payment']):
                # Payment successful
                self.money_supply += loan_info['monthly_payment']
                loan_info['remaining_payments'] -= 1
                
                # Loan completed
                if loan_info['remaining_payments'] <= 0:
                    defaulted_agents.append(agent_id)
            else:
                # Payment failed - mark for bankruptcy
                if isinstance(agent, Consumer):
                    self.bankrupted_consumers += 1
                else:
                    self.bankrupted_firms += 1
                defaulted_agents.append(agent_id)
                
        # Remove completed and defaulted loans
        for agent_id in defaulted_agents:
            del self.loan_registry[agent_id]

    def calculate_inflation(self, previous_price_level, current_price_level):
        """Calculate inflation rate based on price levels"""
        if previous_price_level == 0:
            return 0
        self.inflation_rate = ((current_price_level - previous_price_level) / previous_price_level) * 100
        return self.inflation_rate

    def step(self):
        """Monthly actions of the central bank"""
        self.collect_payments()
        # Calculate average price level from all firms
        current_price_level = np.mean([firm.price for firm in self.model.get_firms()])
        previous_price_level = getattr(self, 'previous_price_level', current_price_level)
        self.calculate_inflation(previous_price_level, current_price_level)
        self.previous_price_level = current_price_level