"""famsplit URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from rest_framework_simplejwt import views as jwt_views
from splitApp import views as split_app_views
from famsplit import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Auth Actions
    path('api/token/', jwt_views.TokenObtainPairView.as_view(),
        name='token_obtain_pair'),
    path('api/token/refresh/', jwt_views.TokenRefreshView.as_view(),
        name='token_refresh'),
    path('create_user/', split_app_views.CreateUserView.as_view(),
        name='create_user'),

    # Group Actions
    path('group/create/', split_app_views.CreateGroupView.as_view(),
        name='create_group'),
    path('group/adduser/', split_app_views.AddMemberToGroupView.as_view(),
        name='add_member'),
    path('group/removeuser/', split_app_views.RemoveMemberFromGroupView.as_view(),
        name='remove_member'),
    path('group/balance/', split_app_views.GetGroupBalanceView.as_view(),
        name='group_balance'),
    path('group/settle/', split_app_views.SettleGroupBalanceView.as_view(),
        name='group_settle_balance'),
    path('group/addpicture/', split_app_views.AddGroupIconView.as_view(),
        name='group_add_picture'),

    # Bill Actions
    path('group/addbill/', split_app_views.AddBillView.as_view(),
        name='add_bill'),
    path('group/editbill/', split_app_views.EditBillView.as_view(),
        name='edit_bill'),
    path('group/billcomment/', split_app_views.AddBillCommentView.as_view(),
        name='bill_comment'),

    # User Actions
    path('user/balance/', split_app_views.GetUserBalanceView.as_view(),
        name='user_balance'),
    path('user/addpicture/', split_app_views.AddUserProfilePictureView.as_view(),
        name='user_add_picture'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
