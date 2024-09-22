from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from .models import User, Expense, UserExpense, Group
from .serializers import UserSerializer, ExpenseSerializer, UserExpenseSerializer
from .permissions import IsOwner, IsGroupAdmin
from rest_framework.permissions import IsAdminUser
from django.contrib.auth.hashers import make_password
from django.shortcuts import get_object_or_404


class ProfileAPIView(APIView):
    """
    This is an example of how you should not handle permissions.
    - Though the 'permission_classes' is overridden, but it is not being called

    Check '.viewsets.ProfileViewSet'
    """
    queryset = User.objects.all()  # Not overridden: parent has no such attribute
    serializer_class = UserSerializer  # Not overridden
    permission_classes = [IsOwner]

    def get(self, request: Request) -> Response:
        user = self.queryset.get(pk=request.user.id)
        return Response(data=UserSerializer(user).data, status=status.HTTP_200_OK)

    def patch(self, request: Request) -> Response:
        deserialized = UserSerializer(data=request.data, partial=True)
        if not deserialized.is_valid():
            return Response(data=deserialized.errors, status=status.HTTP_400_BAD_REQUEST)
        instance = request.user
        if 'password' in deserialized.validated_data:
            print(':: LOG :: ProfileAPIView :: patch | password :: before', deserialized.validated_data['password'])
            deserialized.validated_data['password'] = make_password(deserialized.validated_data['password'])
            print(':: LOG :: ProfileAPIView :: patch | password :: after', deserialized.validated_data['password'])
        instance = deserialized.update(instance, deserialized.validated_data)
        return Response(data=UserSerializer(instance).data, status=status.HTTP_200_OK)

    def get_object(self):  # Not overridden
        pass


class UserListAPIView(ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]


class UserRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]

    def perform_update(self, serializer):
        if 'password' in serializer.validated_data:  # Updating Password
            print(':: LOG :: UserRetrieveUpdateDestroyAPIView :: perform_update | password')
            print(':: Compare :: self.get_object() is serializer.instance ::', self.get_object() is serializer.instance)
            print(':: LOG :: self.get_object() ::', self.get_object())
            print(':: LOG :: serializer.instance ::', serializer.instance)
            # serializer.instance.set_password(serializer.validated_data['password'])  # DOESN'T WORK THIS WAY
            serializer.save(password=make_password(serializer.validated_data['password']))
        else:
            serializer.save()


class ExpenseListAPIView(ListAPIView):
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer
    permission_classes = [IsAdminUser]


class UserExpenseListAPIView(ListAPIView):
    queryset = UserExpense.objects.all()
    serializer_class = UserExpenseSerializer


class AddGroupMemberAPIView(APIView):
    queryset = Group.objects.all()
    permission_classes = [IsGroupAdmin]


