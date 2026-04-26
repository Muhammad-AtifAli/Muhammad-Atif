current_balance = 15000
transactions = []

def check_balance():
    print("Your current balance is:", current_balance)
    transactions.append("Checked Balance: " + str(current_balance))

def withdraw_amount(amount):
    global current_balance

    if amount <= 0:
        print("Please enter a valid amount.")

    elif amount > current_balance:
        print("Insufficient balance.")

    else:
        current_balance = current_balance - amount
        print("Withdrawal successful.")
        print("Remaining balance is:", current_balance)
        transactions.append("Withdraw: " + str(amount))

def mini_statement():
    print("\n----- Mini Statement -----")

    if len(transactions) == 0:
        print("No transactions yet.")
    else:
        for item in transactions:
            print(item)

    print("Current Balance:", current_balance)
