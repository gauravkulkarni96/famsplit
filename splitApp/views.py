from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User as DjangoUser
from django.contrib.auth.hashers import make_password
from django.db import transaction
from collections import defaultdict
import threading

import splitApp.models as splitAppModels
from splitApp import helpers


class CreateUserView(APIView):
    """
    create a user identified by
    username, email and password
    """
    def post(self, request):
        try:
            username = request.data.get("username")
            email = request.data.get("email")
            password = make_password(request.data.get("password"))

            # creating DjangoUser automatically creates custom user
            user_obj = DjangoUser.objects.create(
                username=username,
                email=email,
                password=password,
                is_active=True
            )
            content = {'message': 'User created successfully!'}
            return Response(content)
        except Exception as e:
            print(str(e))
            return Response({'error': str(e)}, status=400)


class CreateGroupView(APIView):
    """
    create new group
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            group_name = request.data.get("groupname")
            created_by = request.user.user

            # create group
            group_obj = splitAppModels.Group.objects.create(
                name=group_name,
                created_by=created_by,
            )

            # Add group creator to the group
            membership_obj = splitAppModels.Membership.objects.create(
                user=created_by, group=group_obj
            )

            content = {'message': 'Group created successfully!'}
            return Response(content)
        except Exception as e:
            print(str(e))
            return Response({'error': str(e)}, status=400)


class AddMemberToGroupView(APIView):
    """
    Add member to group
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            group_name = request.data.get("groupname")
            username = request.data.get("username")

            try:
                group_obj = splitAppModels.Group.objects.get(name=group_name)
            except:
                return Response(
                    {'error': 'Group not found!'},
                    status=404
                    )

            # check if request user is group creator
            if request.user.user != group_obj.created_by:
                return Response(
                    {'error': 'Only group creator can add members'},
                    status=403
                    )
            try:
                user_obj = splitAppModels.User.objects.get(user__username=username)
            except:
                return Response(
                    {'error': 'User not found!'},
                    status=404
                    )

            # Add member to group
            membership_obj, created = splitAppModels.Membership.objects.get_or_create(
                user=user_obj, group=group_obj
            )
            if not created:
                return Response(
                    {'error': 'User already present in group!'},
                    status=400
                    )

            content = {'message': 'Member added successfully!'}
            return Response(content)
        except Exception as e:
            print(str(e))
            return Response({'error': str(e)}, status=400)


class RemoveMemberFromGroupView(APIView):
    """
    Remove member from group if no balance pending
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            group_name = request.data.get("groupname")
            username = request.data.get("username")

            try:
                group_obj = splitAppModels.Group.objects.get(name=group_name)
            except:
                return Response(
                    {'error': 'Group not found!'},
                    status=404
                    )

            # check if request user is group creator
            if request.user.user != group_obj.created_by:
                return Response(
                    {'error': 'Only group creator can remove members'},
                    status=403
                    )
            try:
                user_obj = splitAppModels.User.objects.get(user__username=username)
                membership_obj = splitAppModels.Membership.objects.get(
                    user=user_obj, group=group_obj
                )
            except:
                return Response(
                    {'error': 'User not found in group!'},
                    status=404
                    )

            # check if user who is to be removed owes
            # any balance in the group
            owe_map = helpers.compute_group_user_balance(user_obj, group_obj)
            if owe_map:
                return Response(
                    {'error': 'User has unsettled balances. Can not be removed!'},
                    status=400
                    )

            # remove user from group if balances are settled
            membership_obj.delete()
            content = {'message': 'Member removed successfully!'}
            return Response(content)
        except Exception as e:
            print(str(e))
            return Response({'error': str(e)}, status=400)


class AddBillView(APIView):
    """
    Create new bill
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            group_name = request.data.get("groupname")
            user = request.user.user

            try:
                group_obj = splitAppModels.Group.objects.get(name=group_name)
            except:
                return Response(
                    {'error': 'Group not found!'},
                    status=404
                    )

            bill_title = request.data.get("title")
            bill_amount = float(request.data.get("amount"))

            split_type = request.data.get("split_type")
            split_data = request.data.get("split_data", {})
            pay_data = request.data.get("pay_data")

            # validate data sent in bill.
            # split amounts/percentages should match total
            is_valid, msg = helpers.validate_bill_split(bill_amount, split_type,
                                                    split_data, pay_data, group_obj)

            if not is_valid:
                return Response({'error': msg}, status=400)

            # calculate expenses and payments on the basis of split data
            expense_data = helpers.compute_expense(bill_amount, split_type,
                                                    split_data, pay_data, group_obj)
            payments_data = helpers.compute_payments(expense_data)

            # create Bill record
            bill_object = splitAppModels.Bill.objects.create(
                title=bill_title, group=group_obj,
                added_by=request.user.user, bill_amount=bill_amount
                )

            # save all expenses and payments atomically
            # to handle concurrency issues
            with transaction.atomic():
                for user, expense in expense_data.items():
                    if expense != [0,0]:
                        expense_obj = splitAppModels.Expense(
                            bill=bill_object, user=user,
                            amount_paid=expense[0], amount_owed=expense[1]
                            )
                        expense_obj.save()

                for payment in payments_data:
                    payment_obj = splitAppModels.Payment(
                        payer = payment["from"],
                        receiver = payment["to"],
                        amount = payment["amount"],
                        bill=bill_object
                    )
                    payment_obj.save()

            user_list = [expense_data.keys()]

            # auto settle group balances between 2 users if
            # overall owe amount is 0 spanning accross multiple groups
            # Running in background thread as this could be complex
            # and take more time depending on users/groups
            threading.Thread(
                target=helpers.auto_settle,
                args = (user_list)
            ).start()

            content = {'message': 'Bill added successfully!'}
            return Response(content)
        except Exception as e:
            print(str(e))
            return Response({'error': str(e)}, status=400)


class EditBillView(APIView):
    """
    Edit already created bill
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            user = request.user.user
            bill_id = request.data.get("bill_id")

            try:
                bill_object = splitAppModels.Bill.objects.get(id=bill_id)
            except:
                return Response(
                    {'error': 'Bill not found!'},
                    status=404
                    )

            bill_title = request.data.get("title")
            bill_amount = float(request.data.get("amount"))

            split_type = request.data.get("split_type")
            split_data = request.data.get("split_data", {})
            pay_data = request.data.get("pay_data")

            # validate updated bill details
            is_valid, msg = helpers.validate_bill_split(
                bill_amount, split_type, split_data, pay_data, bill_object.group
            )

            if not is_valid:
                return Response({'error': msg}, status=400)

            # compute payments and expenses for new data
            expense_data = helpers.compute_expense(
                bill_amount, split_type, split_data, pay_data, bill_object.group
            )
            payments_data = helpers.compute_payments(expense_data)

            bill_object.title = bill_title
            bill_object.bill_amount = bill_amount
            bill_object.save()

            # create new payments and expenses and delete older ones
            # atomically to handle concurrency.
            with transaction.atomic():
                splitAppModels.Expense.objects.filter(bill=bill_object).delete()
                splitAppModels.Payment.objects.filter(bill=bill_object).delete()

                for user, expense in expense_data.items():
                    if expense != [0,0]:
                        expense_obj = splitAppModels.Expense(
                            bill=bill_object, user=user,
                            amount_paid=expense[0], amount_owed=expense[1]
                        )
                        expense_obj.save()

                for payment in payments_data:
                    payment_obj = splitAppModels.Payment(
                        payer = payment["from"],
                        receiver = payment["to"],
                        amount = payment["amount"],
                        bill=bill_object
                    )
                    payment_obj.save()

            content = {'message': 'Bill updated successfully!'}
            return Response(content)
        except Exception as e:
            print(str(e))
            return Response({'error': str(e)}, status=400)


class GetGroupBalanceView(APIView):
    """
    Get balance amounts in a group for
    logged in user
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        try:
            group_name = request.data.get("groupname")
            user = request.user.user

            try:
                group_obj = splitAppModels.Group.objects.get(name=group_name)
            except:
                return Response(
                    {'error': 'Group not found!'},
                    status=404
                    )
            owe_map = helpers.compute_group_user_balance(user, group_obj)
            return Response(owe_map)
        except Exception as e:
            print(str(e))
            return Response({'error': str(e)}, status=400)


class SettleGroupBalanceView(APIView):
    """
    Settle group balance between 2 users
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            group_name = request.data.get("groupname")
            username = request.data.get("username")
            user = request.user.user
            try:
                other_user = splitAppModels.User.objects.get(user__username=username)
            except:
                return Response(
                    {'error': 'User not found!'},
                    status=404
                    )
            try:
                group_obj = splitAppModels.Group.objects.get(name=group_name)
            except:
                return Response(
                    {'error': 'Group not found!'},
                    status=404
                    )

            context, status= helpers.settle_group_balance(user, other_user, group_obj)
            return Response(context, status)
        except Exception as e:
            print(str(e))
            return Response({'error': str(e)}, status=400)


class GetUserBalanceView(APIView):
    """
    get overall balance for
    logged in user
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        try:
            user = request.user.user

            owe_map = helpers.compute_overall_user_balance(user)
            print(owe_map)
            return Response(owe_map)
        except Exception as e:
            print(str(e))
            return Response({'error': str(e)}, status=400)


class AddUserProfilePictureView(APIView):
    """
    add profile picture for a user
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            user = request.user.user
            image = request.data.get("image")

            if not image:
                return Response(
                    {'error': 'Image not sent in request!'},
                    status=400
                    )
            user.profile_picture = image
            user.save()

            content = {
                'message': 'User profile pic updated successfully!',
                "image": user.profile_picture.url
            }
            return Response(content)
        except Exception as e:
            print(str(e))
            return Response({'error': str(e)}, status=400)


class AddGroupIconView(APIView):
    """
    add group icon for a user
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            user = request.user.user
            group_name = request.data.get("groupname")
            image = request.data.get("image")

            if not image:
                return Response(
                    {'error': 'Image not sent in request!'},
                    status=400
                    )
            try:
                group_obj = splitAppModels.Group.objects.get(name=group_name)
            except:
                return Response(
                    {'error': 'Group not found!'},
                    status=404
                    )
            if not user == group_obj.created_by:
                return Response(
                    {'error': 'Only group owner can add group icon!'},
                    status=403
                    )

            group_obj.group_icon = image
            group_obj.save()

            content = {
                'message': 'Group icon updated successfully!',
                "image": group_obj.group_icon.url
            }
            return Response(content)
        except Exception as e:
            print(str(e))
            return Response({'error': str(e)}, status=400)


class AddBillCommentView(APIView):
    """
    add note/comment/image to a bill
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            user = request.user.user
            bill_id = request.data.get("bill_id")
            image = request.data.get("image")
            comment = request.data.get("comment")

            if not (image or comment):
                return Response(
                    {'error': 'Comment/Image not sent in request!'},
                    status=400
                    )
            try:
                bill_obj = splitAppModels.Bill.objects.get(id=bill_id)
            except:
                return Response(
                    {'error': 'Bill not found!'},
                    status=404
                    )

            user_is_member = splitAppModels.Membership.objects.filter(
                group=bill_obj.group, user=user
            ).exists()

            if not user_is_member:
                return Response(
                    {'error': 'You are not a member of the bill group!'},
                    status=403
                    )

            splitAppModels.Note.objects.create(
                bill=bill_obj, image=image, text=comment
            )

            content = {
                'message': 'Comment added to bill successfully!',
            }
            return Response(content)
        except Exception as e:
            print(str(e))
            return Response({'error': str(e)}, status=400)
