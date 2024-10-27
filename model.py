# model.py
from mesa import Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
import numpy as np
from agents import Firm, CentralBank, Consumer
import networkx as nx

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
        self.transactions = []
        self.G = nx.DiGraph()
        
        # Create Central Bank
        self.central_bank = CentralBank(0, self, initial_money_supply, base_interest_rate)
        self.schedule.add(self.central_bank)
        self.G.add_node(0, type="bank")
        
        # Create Firms
        for i in range(num_firms):
            firm = Firm(i + 1, self, initial_firm_capital, market_volatility)
            self.schedule.add(firm)
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(firm, (x, y))
            self.G.add_node(firm.unique_id, type="firm")
        
        # Create Consumers
        for i in range(num_consumers):
            consumer = Consumer(i + num_firms + 1, self, initial_consumer_money, satisfaction_threshold)
            self.schedule.add(consumer)
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(consumer, (x, y))
            self.G.add_node(consumer.unique_id, type="consumer")
        
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
                "Average Price": lambda m: self.get_average_price(),
                "Economic Health Index": lambda m: self.get_economic_health_index(),
            }
        )

    def add_transaction(self, transaction):
        self.transactions.append(transaction)
        self.G.add_edges_from([(transaction.sender.unique_id, transaction.receiver.unique_id, 
                                {"amount": transaction.amount, "transactions": transaction.transaction_type})])

    def get_graph_data(self):
        # Prepare data for Plotly visualization
        edges = self.G.edges(data=True)
        x = []
        y = []
        text = []
        
        for edge in edges:
            x.append(edge[0])  # sender
            y.append(edge[1])  # receiver
            text.append(f"Amount: {edge[2]['amount']}")
        
        return x, y, text

    # model.py
    def step(self):
        self.schedule.step()
        
        # Update inflation rate
        self.central_bank.update_inflation_rate([agent.price for agent in self.schedule.agents 
                                                if isinstance(agent, Firm) and not agent.bankrupt])
        
        # Check bankruptcies
        self.check_bankruptcies()
        
        # Distribute employment
        self.distribute_employment()
        
        # Firms that are at risk of bankruptcy can request loans
        for agent in self.schedule.agents:
            if isinstance(agent, Firm) and not agent.bankrupt:
                if agent.capital < agent.initial_capital * self.bankruptcy_threshold:
                    agent.request_loan(50000)  # Example loan amount

        self.datacollector.collect(self)


    def get_total_transactions(self):
        return len(self.transactions)
    
    def distribute_employment(self, initial_employment_rate=0.6):
    # Limit initial employment to a fixed percentage
        available_consumers = [agent for agent in self.schedule.agents 
                            if isinstance(agent, Consumer) and not agent.bankrupt]
        active_firms = [agent for agent in self.schedule.agents 
                        if isinstance(agent, Firm) and not agent.bankrupt]

        active_firms.sort(key=lambda x: x.capital, reverse=True)
        
        # Calculate initial employment target based on rate
        initial_employment_target = int(initial_employment_rate * len(available_consumers))
        currently_employed = 0
        
        for firm in active_firms:
            # Determine max number of employees firm can support based on capital and production capacity
            max_employees = min(
                firm.production_capacity,
                int(firm.capital / (firm.wage * 3))
            )
            
            # Determine needed employees while respecting the initial employment target
            needed_employees = max(0, max_employees - len(firm.employees))
            new_hires = min(needed_employees, initial_employment_target - currently_employed, len(available_consumers))
            
            # Hire new employees based on available slots and the initial employment target
            for _ in range(new_hires):
                if available_consumers:
                    consumer = available_consumers.pop(0)
                    consumer.employer = firm
                    firm.employees.append(consumer)
                    currently_employed += 1
                else:
                    break  # Exit if no more available consumers

            # If the initial employment target has been met, stop
            if currently_employed >= initial_employment_target:
                break

    
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

    def get_economic_health_index(self):
        employment_weight = 0.3
        satisfaction_weight = 0.2
        bankruptcy_weight = 0.5  # Adjusted to emphasize bankruptcy in index
        
        employment_rate = self.get_employment_rate()
        satisfaction = self.get_average_satisfaction()
        
        total_agents = self.num_consumers + self.num_firms
        bankruptcy_rate = 1 - ((self.central_bank.bankrupted_firms + self.central_bank.bankrupted_consumers) / total_agents)
        
        return (employment_rate * employment_weight +
                satisfaction * satisfaction_weight +
                bankruptcy_rate * bankruptcy_weight)
