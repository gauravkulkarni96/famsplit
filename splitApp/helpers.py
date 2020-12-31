from splitApp.models import Membership, User, Payment, Expense, Bill
from collections import defaultdict
from django.db import transaction
from queue import PriorityQueue
from django.db.models import Q
import math

def validate_bill_split(bill_amount, split_type, split_data, pay_data, group_obj):
    """
    validate the split amount and pay amount with total amount
    """
    pay_amount = 0
    for amount in pay_data.values():
        pay_amount += float(amount)
    if pay_amount != bill_amount:
        return False, "Bill and pay amount mismatch."

    usernames = list(set(split_data.keys()).union(set(pay_data.keys())))
    users_count = Membership.objects.filter(
        user__user__username__in=usernames, group=group_obj
        ).count()

    if users_count != len(usernames):
        return False, "Invalid member passed."

    split_total = 0
    for amount in split_data.values():
        split_total += float(amount)

    if split_type == "fixed":
        # sum of splits should be equal to total amount
        if split_total != bill_amount:
            return False, "Bill and split amount mismatch."
    elif split_type == "percentage":
        # sum of split percentages should be 100
        if split_total != 100:
            return False, "Bill and split amount mismatch."
    elif split_type != "equal":
        return False, "Invalid split type"
    return True, "valid"


def compute_expense(bill_amount, split_type, split_data, pay_data, group_obj):
    """
    compute amounts owed and paid by users in group
    """
    memberships = Membership.objects.filter(group=group_obj)
    user_object_map = {
        membership.user.user.username: membership.user for membership in memberships
    }

    expense_data = {
        user_obj:[0,0] for user_obj in user_object_map.values()
    }

    for username, amount in pay_data.items():
        user = user_object_map[username]
        expense_data[user][0] = float(amount)

    if split_type == "fixed":
        for username, amount in split_data.items():
            user = user_object_map[username]
            expense_data[user][1] = float(amount)
    elif split_type == "percentage":
        for username, percentage in split_data.items():
            user = user_object_map[username]
            expense_data[user][1] = float(percentage*bill_amount/100)
    else: # split_type -> equal
        owe_user_list = split_data.keys()

        # if owe_list is empty, divide between all group members
        if not len(owe_user_list):
            owe_user_list = [
                membership.user.user.username for membership in memberships
                ]

            each_share = math.floor(bill_amount/len(owe_user_list) * 100) / 100

            # calculate excess amount as there could be difference
            # while rounding amount for shares.
            excess_amount = bill_amount - (each_share*len(owe_user_list))

            divide_excess_amount_index = int(excess_amount/0.01)
            for username in owe_user_list:
                user = user_object_map[username]
                expense_data[user][1] = float(each_share)
                if divide_excess_amount_index > 0:
                    expense_data[user][1] = round(expense_data[user][1]+0.01, 2)
                    divide_excess_amount_index -= 1
    return expense_data
            

def compute_payments(expense_data):
    """
    compute payments needed to settle bills
    """
    positive_balances = []
    negative_balances = []
    
    for user, expense in expense_data.items():
        balance = expense[0]-expense[1]
        if  balance < 0:
            negative_balances.append([user, balance])
        elif balance > 0:
            positive_balances.append([user, balance])

    negative_balances.sort(key=lambda x: x[1])
    positive_balances.sort(key=lambda x: x[1], reverse=True)

    positive_index=0
    negative_index=0

    payments = []

    while positive_index<len(positive_balances) and \
                negative_index<len(negative_balances):
        amount = min(
            positive_balances[positive_index][1],
            -1*negative_balances[negative_index][1]
            )
        data = {
            "from": negative_balances[negative_index][0],
            "to": positive_balances[positive_index][0],
            "amount": amount
            }
        payments.append(data)
        positive_balances[positive_index][1] -= amount
        negative_balances[negative_index][1] += amount

        if positive_balances[positive_index][1] == 0:
            positive_index += 1
        if negative_balances[negative_index][1] == 0:
            negative_index += 1
    return payments


def simplify_payments(balances, user):
    """
    simplify payments using priority queue
    """
    positive_queue = PriorityQueue()
    negative_queue = PriorityQueue()

    for group_user, balance in balances.items():
        if balance < 0:
            negative_queue.put((balance, [group_user, round(balance,2)]))
        else:
            positive_queue.put((-1*balance, [group_user, round(balance,2)]))

    payments = defaultdict(lambda:0)
    
    while not (positive_queue.empty() or negative_queue.empty()):
        positive_elem = positive_queue.get()[1]
        negative_elem = negative_queue.get()[1]

        amount = min(
            positive_elem[1],
            -1*negative_elem[1]
        )
        if negative_elem[0] == user:
            payments[positive_elem[0].user.username] -= amount
        elif positive_elem[0] == user:
            payments[negative_elem[0].user.username] += amount
        positive_elem[1] -= amount
        if positive_elem[1] > 0:
            positive_queue.put((-1*positive_elem[1], positive_elem))
        negative_elem[1] += amount
        if negative_elem[1]<0:
            negative_queue.put((negative_elem[1], negative_elem))
    return payments


def compute_group_user_balance(user, group_obj):
    """
    compute amounts owed to user in a group
    """
    owe_map = defaultdict(lambda:0)
    if not group_obj.simplify_payments:
        # compute balances using payments
        # if simplify payments is turned off
        payments = Payment.objects.filter(
            (Q(payer=user) | Q(receiver=user)) & Q(bill__group=group_obj)
        )

        for payment in payments:
            if payment.payer == user:
                owe_map[payment.receiver.user.username] -= payment.amount
            else:
                owe_map[payment.payer.user.username] += payment.amount
    else:
        # compute balances using expenses
        # if simplify payments is turned on
        expenses = Expense.objects.filter(
            bill__group=group_obj
        )
        balances = defaultdict(lambda:0)
        for expense in expenses:
            balances[expense.user] += expense.amount_paid
            balances[expense.user] -= expense.amount_owed
        owe_map = simplify_payments(balances, user)
    owe_map = {
        user:round(balance,2) \
        for user, balance in owe_map.items() \
        if round(balance,2) != 0
    }
    return owe_map


def compute_overall_user_balance(user):
    """
    compute overall amounts owed to user by other users
    """
    owe_map = defaultdict(lambda:0)
    payments = Payment.objects.filter(
        Q(payer=user) | Q(receiver=user)
    )

    for payment in payments:
        if payment.payer == user:
            owe_map[payment.receiver.user.username] -= payment.amount
        else:
            owe_map[payment.payer.user.username] += payment.amount
    owe_map = {
        user:round(balance,2) \
        for user, balance in owe_map.items() \
        if round(balance,2) != 0
    }
    return owe_map


def settle_group_balance(user, other_user, group_obj):
    owe_map = compute_group_user_balance(user, group_obj)

    if other_user.user.username not in owe_map:
        return {'error': 'No balance pending!'}, 400

    amount = owe_map[other_user.user.username]

    bill_object = Bill.objects.create(
        title="Settle Balance", group=group_obj,
        added_by=user, bill_amount=abs(amount)
    )

    # create reverse bill to settle the amount
    # between 2 users
    with transaction.atomic():
        payer=other_user
        ower=user
        if amount < 0:
            payer=user
            ower=other_user
        amount = abs(amount)
        expense_obj_1 = Expense(
            bill=bill_object, user=payer,
            amount_paid=amount, amount_owed=0
        ).save()

        expense_obj_2 = Expense(
            bill=bill_object, user=ower,
            amount_paid=0, amount_owed=amount
        ).save()
        
        payment_obj = Payment(
            payer = ower,
            receiver = payer,
            amount = amount,
            bill=bill_object
        ).save()
    return {'message': 'Balance Settled!'}, 200


def auto_settle(user_list):
    """
    auto settle group balances if
    overall balance of two users is 0
    """
    overall_user_balances = {}

    # get overall balances for all users in recently added bill
    for user in user_list:
        overall_user_balances[user] = compute_overall_user_balance(user)
    
    for user in overall_user_balances.keys():
        user_membership_list = Membership.objects.filter(user=user)

        # check for user balances in all groups he's a member of
        for membership in user_membership_list:
            group = membership.group
            group_balance = compute_group_user_balance(user, group)

            for user_owed in group_balance.keys():
                # settle group balance if there is no overall balance
                # between 2 users but group balance is pending.
                if user_owed not in overall_user_balances[user]:
                    user_owed_obj = User.objects.get(user__username=user_owed)
                    settle_group_balance(user, user_owed_obj, group)
    return True
