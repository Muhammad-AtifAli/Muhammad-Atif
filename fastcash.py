current_balance = 15000

def fast_cash(option):
    global current_balance

    if option == "1":
        amount = 500
    elif option == "2":
        amount = 1000
    elif option == "3":
        amount = 2000
    elif option == "4":
        amount = 5000
    else:
        print("Invalid option")
        return

    if amount > current_balance:
        print("Insufficient balance.")
    else:
        current_balance = current_balance - amount
        print("Fast cash withdrawal successful.")
        print("Withdrawn amount:", amount)
        print("Remaining balance:", current_balance)