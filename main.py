from run_visualization import run_simulation
import argparse

def main():
    parser = argparse.ArgumentParser(description='Run Economy Simulation')
    parser.add_argument('--consumers', type=int, default=100,
                      help='Number of consumers (default: 100)')
    parser.add_argument('--firms', type=int, default=10,
                      help='Number of firms (default: 10)')
    parser.add_argument('--money-supply', type=int, default=1000000,
                      help='Initial money supply (default: 1000000)')
    parser.add_argument('--interest-rate', type=float, default=0.05,
                      help='Base interest rate (default: 0.05)')
    parser.add_argument('--firm-capital', type=int, default=100000,
                      help='Initial firm capital (default: 100000)')
    parser.add_argument('--consumer-money', type=int, default=1000,
                      help='Initial consumer money (default: 1000)')
    parser.add_argument('--steps', type=int, default=100,
                      help='Simulation steps (default: 100)')
    
    args = parser.parse_args()
    
    model = run_simulation(
        steps=args.steps,  # Changed from simulation_steps to steps
        num_consumers=args.consumers,
        num_firms=args.firms,
        initial_money_supply=args.money_supply,
        base_interest_rate=args.interest_rate,
        initial_firm_capital=args.firm_capital,
        initial_consumer_money=args.consumer_money
    )
    
    # Print final statistics
    print("\nFinal Simulation Statistics:")
    print(f"Inflation Rate: {model.central_bank.inflation_rate:.2f}%")
    print(f"Employment Rate: {model.get_employment_rate()*100:.2f}%")
    print(f"Average Consumer Satisfaction: {model.get_average_satisfaction():.2f}")
    print(f"Total Bankruptcies - Firms: {model.central_bank.bankrupted_firms}")
    print(f"Total Bankruptcies - Consumers: {model.central_bank.bankrupted_consumers}")

if __name__ == "__main__":
    main()