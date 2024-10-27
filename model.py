# model.py
from mesa import Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
import numpy as np
from agents import Firm, CentralBank, Consumer

class EconomyModel(Model):
    def __init__(self, num_consumers, num_firms, initial_money_supply, base_interest_rate,
                 initial_firm_capital, initial_consumer_money, market_volatility=0.2,
                 bankruptcy_threshold=0.3, satisfaction_threshold=0.5, width=20, height=20):
        super().__init__()
        self.num_consumers = num_consumers
        self.num_firms = num_firms
        self.grid = MultiGrid(width, height, True)
        self.schedule = RandomActivation(self)
        self.bankruptcy_threshold = bankruptcy_threshold
        
        # Create Central Bank
        self.central_bank = CentralBank(0, self, initial_money_supply, base_interest_rate)
        self.schedule.add(self.central_bank)
        
        # Create Firms
        for i in range(num_firms):
            firm = Firm(i + 1, self, initial_firm_capital, market_volatility)
            self.schedule.add(firm)
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(firm, (x, y))
        
        # Create Consumers
        for i in range(num_consumers):
            consumer = Consumer(i + num_firms + 1, self, initial_consumer_money, satisfaction_threshold)
            self.schedule.add(consumer)
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(consumer, (x, y))
        
        self.distribute_employment()
        
        # Enhanced Data Collection
        self.datacollector = DataCollector(
            model_reporters={
                "Inflation Rate": lambda m: m.central_bank.inflation_rate,
                "Employment Rate": self.get_employment_rate,
                "Average Satisfaction": self.get_average_satisfaction,
                "Bankrupted Firms": lambda m: m.central_bank.bankrupted_firms,
                "Bankrupted Consumers": lambda m: m.central_bank.bankrupted_consumers,
                "Money Supply": lambda m: m.central_bank.money_supply,
                "Total Loans": lambda m: m.central_bank.total_loans,
                "Average Price": self.get_average_price,
                "Average Credit Score": self.get_average_credit_score,
                "Economic Health Index": self.get_economic_health_index
            }
        )
    
    def step(self):
        self.schedule.step()
        self.central_bank.update_inflation_rate([agent.price for agent in self.schedule.agents 
                                               if isinstance(agent, Firm) and not agent.bankrupt])
        self.check_bankruptcies()
        self.distribute_employment()
        self.datacollector.collect(self)
    
    def distribute_employment(self):
        available_consumers = [agent for agent in self.schedule.agents 
                             if isinstance(agent, Consumer) and not agent.employer and not agent.bankrupt]
        
        active_firms = [agent for agent in self.schedule.agents 
                       if isinstance(agent, Firm) and not agent.bankrupt]
        
        active_firms.sort(key=lambda x: x.capital, reverse=True)
        
        for firm in active_firms:
            max_employees = min(
                firm.production_capacity,
                int(firm.capital / (firm.wage * 3))
            )
            
            needed_employees = max_employees - len(firm.employees)
            if needed_employees > 0:
                available_consumers.sort(key=lambda x: x.credit_score, reverse=True)
                for _ in range(min(needed_employees, len(available_consumers))):
                    consumer = available_consumers.pop(0)
                    consumer.employer = firm
                    firm.employees.append(consumer)
    
    def check_bankruptcies(self):
        for agent in self.schedule.agents:
            if isinstance(agent, Firm):
                if not agent.bankrupt and agent.capital < agent.initial_capital * self.bankruptcy_threshold:
                    agent.bankrupt = True
                    self.central_bank.bankrupted_firms += 1
                    for employee in agent.employees:
                        employee.employer = None
                    agent.employees.clear()
            elif isinstance(agent, Consumer):
                if not agent.bankrupt and agent.money < agent.initial_money * self.bankruptcy_threshold:
                    agent.bankrupt = True
                    self.central_bank.bankrupted_consumers += 1
                    if agent.employer:
                        agent.employer.employees.remove(agent)
                        agent.employer = None
    
    def get_employment_rate(self):
        active_consumers = [agent for agent in self.schedule.agents 
                          if isinstance(agent, Consumer) and not agent.bankrupt]
        if not active_consumers:
            return 0
        employed = len([c for c in active_consumers if c.employer])
        return employed / len(active_consumers)
    
    def get_average_satisfaction(self):
        active_consumers = [agent for agent in self.schedule.agents 
                          if isinstance(agent, Consumer) and not agent.bankrupt]
        if not active_consumers:
            return 0
        return sum(c.satisfaction for c in active_consumers) / len(active_consumers)
    
    def get_average_price(self):
        active_firms = [agent for agent in self.schedule.agents 
                       if isinstance(agent, Firm) and not agent.bankrupt]
        if not active_firms:
            return 0
        return sum(f.price for f in active_firms) / len(active_firms)
    
    def get_average_credit_score(self):
        active_agents = [agent for agent in self.schedule.agents 
                        if (isinstance(agent, (Consumer, Firm)) and 
                            not agent.bankrupt)]
        if not active_agents:
            return 0
        return sum(a.credit_score for a in active_agents) / len(active_agents)
    
    def get_economic_health_index(self):
        employment_weight = 0.3
        satisfaction_weight = 0.2
        credit_weight = 0.2
        bankruptcy_weight = 0.3
        
        employment_rate = self.get_employment_rate()
        satisfaction = self.get_average_satisfaction()
        credit_score = self.get_average_credit_score()
        
        total_agents = self.num_consumers + self.num_firms
        bankruptcy_rate = 1 - ((self.central_bank.bankrupted_firms + self.central_bank.bankrupted_consumers) / total_agents)
        
        return (employment_rate * employment_weight +
                satisfaction * satisfaction_weight +
                credit_score * credit_weight +
                bankruptcy_rate * bankruptcy_weight)
