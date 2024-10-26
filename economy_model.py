import numpy as np
from typing import List, Optional

class CentralBank:
    def __init__(self, initial_money_supply: float, base_interest_rate: float):
        self.money_supply = initial_money_supply
        self.base_interest_rate = base_interest_rate
        self.total_loans = 0
        self.price_history = []
        self.inflation_rate = 0
        self.bankrupted_firms = 0
        self.bankrupted_consumers = 0
        
    def calculate_loan_interest_rate(self, credit_score: float) -> float:
        """Calculate interest rate based on credit score and base rate"""
        return self.base_interest_rate * (2 - credit_score)
    
    def approve_loan(self, amount: float, credit_score: float) -> tuple[bool, float]:
        """Determine if loan is approved and at what interest rate"""
        if credit_score < 0.3 or amount > self.money_supply * 0.1:
            return False, 0
        
        interest_rate = self.calculate_loan_interest_rate(credit_score)
        self.total_loans += amount
        self.money_supply += amount  # Money creation through lending
        return True, interest_rate
    
    def update_inflation_rate(self, current_prices: List[float]):
        """Calculate inflation rate based on price changes"""
        if not self.price_history:
            self.price_history.append(current_prices)
            self.inflation_rate = 0
            return
        
        if len(current_prices) == 0:
            return
            
        old_avg_price = np.mean(self.price_history[-1]) if self.price_history[-1] else 0
        new_avg_price = np.mean(current_prices)
        
        if old_avg_price > 0:
            self.inflation_rate = ((new_avg_price - old_avg_price) / old_avg_price) * 100
        
        self.price_history.append(current_prices)
        if len(self.price_history) > 12:  # Keep only last 12 periods
            self.price_history.pop(0)

class Firm:
    def __init__(self, initial_capital: float, market_volatility: float):
        self.capital = initial_capital
        self.initial_capital = initial_capital
        self.price = initial_capital * 0.1  # Initial price set to 10% of capital
        self.production_capacity = int(initial_capital / 1000)  # 1 unit per 1000 capital
        self.inventory = 0
        self.employees: List[Consumer] = []
        self.loans: List[tuple[float, float]] = []  # (amount, interest_rate)
        self.market_volatility = market_volatility
        self.bankrupt = False
        self.credit_score = 1.0
        self.wage = 100  # Base wage
        
    def adjust_price(self, demand: int):
        """Adjust price based on demand and market conditions"""
        supply = self.production_capacity
        
        # Basic supply-demand adjustment
        if demand > supply:
            self.price *= 1.1
        elif demand < supply:
            self.price *= 0.9
            
        # Add random market volatility
        if np.random.random() < self.market_volatility:
            self.price *= np.random.uniform(0.8, 1.2)
            
        # Ensure minimum price
        self.price = max(self.price, self.production_capacity * 10)
    
    def produce(self):
        """Produce goods based on capacity and update capital"""
        if self.bankrupt:
            return
            
        # Production costs
        labor_cost = sum(self.wage for _ in self.employees)
        material_cost = self.production_capacity * 50  # Base material cost
        
        total_cost = labor_cost + material_cost
        
        if total_cost > self.capital:
            self.production_capacity = max(1, int(self.capital / (labor_cost + 50)))
            
        self.capital -= total_cost
        self.inventory = self.production_capacity
        
        # Update credit score based on capital ratio
        self.credit_score = min(1.0, self.capital / self.initial_capital)
    
    def hire(self, consumer: 'Consumer') -> bool:
        """Attempt to hire a consumer"""
        if self.bankrupt or len(self.employees) >= self.production_capacity:
            return False
            
        self.employees.append(consumer)
        return True
    
    def fire(self, consumer: 'Consumer'):
        """Fire a consumer"""
        if consumer in self.employees:
            self.employees.remove(consumer)
    
    def pay_wages(self):
        """Pay wages to employees"""
        if self.bankrupt:
            return
            
        total_wages = sum(self.wage for _ in self.employees)
        if total_wages > self.capital:
            self.bankrupt = True
            for employee in self.employees:
                employee.employer = None
            self.employees.clear()
            return
            
        for employee in self.employees:
            self.capital -= self.wage
            employee.money += self.wage
    
    def service_loans(self):
        """Pay interest on outstanding loans"""
        if self.bankrupt:
            return
            
        for amount, rate in self.loans:
            interest_payment = amount * rate
            if interest_payment > self.capital:
                self.bankrupt = True
                return
            self.capital -= interest_payment

class Consumer:
    def __init__(self, initial_money: float, satisfaction_threshold: float):
        self.money = initial_money
        self.initial_money = initial_money
        self.employer: Optional[Firm] = None
        self.satisfaction = 1.0
        self.loans: List[tuple[float, float]] = []  # (amount, interest_rate)
        self.bankrupt = False
        self.credit_score = 1.0
        self.satisfaction_threshold = satisfaction_threshold
        self.current_firm: Optional[Firm] = None
        
    def decide_purchase(self, firms: List[Firm]) -> Optional[Firm]:
        """Decide which firm to purchase from based on price and satisfaction"""
        if self.bankrupt or not firms:
            return None
            
        available_firms = [f for f in firms if not f.bankrupt and f.inventory > 0]
        if not available_firms:
            return None
            
        # Consider price and previous satisfaction
        weights = []
        for firm in available_firms:
            if firm.price > self.money:
                weights.append(0)
            else:
                # Higher weight for lower prices and firms we were satisfied with
                price_factor = 1 / (firm.price + 1)
                satisfaction_factor = 1.0
                if firm == self.current_firm:
                    satisfaction_factor = self.satisfaction
                weights.append(price_factor * satisfaction_factor)
                
        if not any(weights):
            return None
            
        # Normalize weights
        weights = np.array(weights) / sum(weights)
        
        # Choose firm probabilistically based on weights
        chosen_firm = np.random.choice(available_firms, p=weights)
        return chosen_firm
    
    def make_purchase(self, firm: Firm):
        """Make a purchase from the chosen firm"""
        if self.bankrupt or firm.bankrupt or firm.inventory <= 0:
            return
            
        if firm.price > self.money:
            # Try to get a loan if can't afford
            needed_loan = firm.price - self.money
            loan_approved, interest_rate = self.try_get_loan(needed_loan)
            if not loan_approved:
                self.satisfaction *= 0.9
                return
                
        self.money -= firm.price
        firm.capital += firm.price
        firm.inventory -= 1
        
        # Update satisfaction based on price fairness
        avg_market_price = firm.price  # This could be improved to consider all firms
        price_satisfaction = 1 - (firm.price - avg_market_price) / avg_market_price
        self.satisfaction = 0.8 * self.satisfaction + 0.2 * price_satisfaction
        self.current_firm = firm
    
    def try_get_loan(self, amount: float) -> tuple[bool, float]:
        """Attempt to get a loan from the central bank"""
        if self.bankrupt:
            return False, 0
            
        # Update credit score based on current money compared to initial money
        self.credit_score = min(1.0, self.money / self.initial_money)
        
        return False, 0  # Simplified - could be expanded to use central bank
    
    def service_loans(self):
        """Pay interest on outstanding loans"""
        if self.bankrupt:
            return
            
        for amount, rate in self.loans:
            interest_payment = amount * rate
            if interest_payment > self.money:
                self.bankrupt = True
                if self.employer:
                    self.employer.fire(self)
                    self.employer = None
                return
            self.money -= interest_payment

class EconomyModel:
    def __init__(self, num_consumers: int, num_firms: int, 
                 initial_money_supply: float, base_interest_rate: float,
                 initial_firm_capital: float, initial_consumer_money: float,
                 market_volatility: float = 0.2, bankruptcy_threshold: float = 0.3,
                 satisfaction_threshold: float = 0.5):
        
        self.central_bank = CentralBank(initial_money_supply, base_interest_rate)
        self.market_volatility = market_volatility
        self.bankruptcy_threshold = bankruptcy_threshold
        
        # Initialize firms
        self.firms = [
            Firm(initial_firm_capital, market_volatility)
            for _ in range(num_firms)
        ]
        
        # Initialize consumers
        self.consumers = [
            Consumer(initial_consumer_money, satisfaction_threshold)
            for _ in range(num_consumers)
        ]
        
        # Initial employment distribution
        self.distribute_employment()
    
    def distribute_employment(self):
        """Distribute consumers among firms as employees"""
        available_consumers = [c for c in self.consumers if not c.employer and not c.bankrupt]
        
        for firm in self.firms:
            if firm.bankrupt:
                continue
                
            # Calculate how many employees the firm can afford
            max_employees = min(
                firm.production_capacity,
                int(firm.capital / (firm.wage * 3))  # Ensure firm can pay 3 periods of wages
            )
            
            while len(firm.employees) < max_employees and available_consumers:
                consumer = available_consumers.pop()
                if firm.hire(consumer):
                    consumer.employer = firm
                    if not available_consumers:
                        break
    
    def step(self):
        """Execute one step of the economy simulation"""
        # Firms produce goods
        for firm in self.firms:
            if not firm.bankrupt:
                firm.produce()
                
        # Pay wages
        for firm in self.firms:
            if not firm.bankrupt:
                firm.pay_wages()
                
        # Consumers make purchases
        np.random.shuffle(self.consumers)  # Randomize order
        for consumer in self.consumers:
            if not consumer.bankrupt:
                chosen_firm = consumer.decide_purchase(self.firms)
                if chosen_firm:
                    consumer.make_purchase(chosen_firm)
        
        # Service loans
        for agent in self.firms + self.consumers:
            if not agent.bankrupt:
                agent.service_loans()
        
        # Adjust prices based on demand
        for firm in self.firms:
            if not firm.bankrupt:
                demand = len([c for c in self.consumers if c.current_firm == firm])
                firm.adjust_price(demand)
        
        # Update central bank metrics
        self.central_bank.update_inflation_rate([f.price for f in self.firms if not f.bankrupt])
        
        # Check for bankruptcies
        self.check_bankruptcies()
        
        # Redistribute employment
        self.distribute_employment()
    
    def check_bankruptcies(self):
        """Check and handle bankruptcies"""
        # Check firms
        for firm in self.firms:
            if not firm.bankrupt and firm.capital < firm.initial_capital * self.bankruptcy_threshold:
                firm.bankrupt = True
                self.central_bank.bankrupted_firms += 1
                # Fire all employees
                for employee in firm.employees:
                    employee.employer = None
                firm.employees.clear()
        
        # Check consumers
        for consumer in self.consumers:
            if not consumer.bankrupt and consumer.money < consumer.initial_money * self.bankruptcy_threshold:
                consumer.bankrupt = True
                self.central_bank.bankrupted_consumers += 1
                if consumer.employer:
                    consumer.employer.fire(consumer)
                    consumer.employer = None
    
    def get_employment_rate(self) -> float:
        """Calculate current employment rate"""
        if not self.consumers:
            return 0
        employed = len([c for c in self.consumers if c.employer and not c.bankrupt])
        total_active = len([c for c in self.consumers if not c.bankrupt])
        return employed / total_active if total_active > 0 else 0
    
    def get_average_satisfaction(self) -> float:
        """Calculate average consumer satisfaction"""
        active_consumers = [c for c in self.consumers if not c.bankrupt]
        if not active_consumers:
            return 0
        return sum(c.satisfaction for c in active_consumers) / len(active_consumers)
    
    def get_firms(self) -> List[Firm]:
        """Return list of firms"""
        return self.firms

if __name__ == "__main__":
    # Test the model with some basic parameters
    model = EconomyModel(
        num_consumers=100,
        num_firms=10,
        initial_money_supply=1000000,
        base_interest_rate=0.05,
        initial_firm_capital=100000,
        initial_consumer_money=1000,
        market_volatility=0.2,
        bankruptcy_threshold=0.3
    )
    
    # Run for a few steps and print basic metrics
    for i in range(10):
        model.step()
        print(f"\nStep {i+1}:")
        print(f"Employment Rate: {model.get_employment_rate()*100:.1f}%")
        print(f"Inflation Rate: {model.central_bank.inflation_rate:.1f}%")
        print(f"Bankruptcies - Firms: {model.central_bank.bankrupted_firms}, "
              f"Consumers: {model.central_bank.bankrupted_consumers}")