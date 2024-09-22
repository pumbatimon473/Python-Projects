"""
URL configuration for splitwise project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.urls import path, include
from .viewsets import CreateUserViewSet, UserExpenseViewSet, GroupViewSet, ListCreateGroupExpenseViewSet
from .viewsets import RetrieveUpdateDestroyGroupExpenseViewSet, ProfileViewSet
from .viewsets import QueryExpenseViewSet, GroupSettleUpViewSet
from .views import ProfileAPIView, UserListAPIView, UserRetrieveUpdateDestroyAPIView, ExpenseListAPIView
from .views import UserExpenseListAPIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.routers import DefaultRouter

"""
Q. How to reverse the URL of a ViewSet's custom action in DRF?
- https://stackoverflow.com/questions/51317534/how-to-reverse-the-url-of-a-viewsets-custom-action-in-django-restframework
- https://djangocentral.com/how-to-use-action-decorator-in-django-rest-framework/

ViewSets:
- https://www.django-rest-framework.org/api-guide/viewsets/

"""
# register the viewset to the default router
router = DefaultRouter()
router.register(r'group_expense', RetrieveUpdateDestroyGroupExpenseViewSet, basename='group-exp')
print(':: LOG :: router.get_urls()', *router.get_urls(), sep='\n:: ')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/token/', TokenObtainPairView.as_view()),
    path('api/token/refresh/', TokenRefreshView.as_view()),
    path('register/user/', CreateUserViewSet.as_view({'post': 'create'})),
    # path('profile/', ProfileAPIView.as_view()),
    path('profile/', ProfileViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update'})),
    path('admins/user/', UserListAPIView.as_view()),
    path('admins/user/<int:pk>/', UserRetrieveUpdateDestroyAPIView.as_view()),
    path('expense/user/', UserExpenseViewSet.as_view({'post': 'create'})),
    path('admins/expense/', ExpenseListAPIView.as_view()),
    path('admins/expense/user/', UserExpenseListAPIView.as_view()),
    path('user/group/', GroupViewSet.as_view({'post': 'create'})),
    path('user/group/<int:pk>/', GroupViewSet.as_view({'patch': 'add_member', 'get': 'retrieve',
                                                       'put': 'update_name', 'delete': 'remove_member'})),
    path('expense/group/<int:group_id>/', ListCreateGroupExpenseViewSet.as_view({'post': 'create',
                                                                                 'get': 'list'})),
    # path('', include(router.urls)),  # default router
    path('expense/group/<int:group_id>/id/<int:pk>/', RetrieveUpdateDestroyGroupExpenseViewSet.as_view({
        'get': 'retrieve', 'delete': 'del_exp_related'
    })),
    path('user/expense/', QueryExpenseViewSet.as_view({'get': 'get_expense'})),
    path('expense/group/<int:group_id>/settle_up/', GroupSettleUpViewSet.as_view({'get': 'settle_up'})),
]
