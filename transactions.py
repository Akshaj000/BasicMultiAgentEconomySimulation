class Transaction:
    def __init__(self, sender, receiver, amount, transaction_type):
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.transaction_type = transaction_type
        self.timestamp = None
