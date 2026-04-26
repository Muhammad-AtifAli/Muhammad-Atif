current_balance = 15000

def check_balance():
    print("Your current balance is:", current_balance)

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
