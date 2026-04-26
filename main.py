#      ATM Project
# 1. User Pin

# import pin
# pin.check_pin()

# 2. Current Balance

# import CurrBal
# CurrBal.check_balance()

# 3. Cash Withdrawal


# import CurrBal 
# import Withdraw

# print("1. Check Balance")
# print("2. Withdraw Amount")

# choice = input("Enter your choice: ")

# if choice == "1":
#     CurrBal.check_balance()
# elif choice == "2":
#     amount = int(input("Enter withdraw amount: "))
#     Withdraw.withdraw_amount(amount)

# else:
#     print("Invalid choice")

# 4. Fast Cash Withdrawal

# import fastcash

# print("Fast Cash Options")
# print("1. 500")
# print("2. 1000")
# print("3. 2000")
# print("4. 5000")

# option = input("Choose fast cash option: ")
# fastcash.fast_cash(option)

#  5.Mini Statement


# import minstat

# while True:
#     print("\n1. Check Balance")
#     print("2. Withdraw Amount")
#     print("3. Mini Statement")
#     print("4. Exit")

#     choice = input("Enter your choice: ")

#     if choice == "1":
#         minstat.check_balance()

#     elif choice == "2":
#         amount = int(input("Enter withdraw amount: "))
#         minstat.withdraw_amount(amount)

#     elif choice == "3":
#         minstat.mini_statement()

#     elif choice == "4":
#         print("Thank you for using ATM")
#         break

#     else:
#         print("Invalid choice")