from django.db.models import F, Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ViewSet

from .enums import Query, SettlementType
from .factories import SettlementStrategyFactory
from .models import User, UserExpense, Group, GroupExpense, ExpensePaidBy, ExpenseSharedBy
from .permissions import IsGroupAdmin, IsGroupAdminOrMember, IsGroupAdminOrExpenseCreator, HasGroupAccess
from .serializers import ExpenseSerializer
from .serializers import QueryUserExpenseSerializer, QueryGroupExpenseSerializer
from .serializers import UserSerializer, UserExpenseSerializer, GroupSerializer, GroupExpenseSerializer
from .utils import build_balance_sheet


class CreateUserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserExpenseViewSet(ModelViewSet):
    queryset = UserExpense.objects.all()
    serializer_class = UserExpenseSerializer
    permission_classes = [IsAuthenticated]

    # Overridden
    def perform_create(self, serializer):
        # Added additional info while saving the instance
        serializer.save(paid_by=self.request.user, created_by=self.request.user)


class GroupViewSet(ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    # NOTE: IsGroupAdmin is an object level permission
    permission_classes = [IsAuthenticated, IsGroupAdmin]

    # Overridden
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    """
    CUSTOM ACTIONS:
    
    'detail' argument:
    - True: indicates the specified action is for a single instance of the resource
    - False: indicated the specified action is applicable to the entire resource collection
    
    Ref: https://djangocentral.com/how-to-use-action-decorator-in-django-rest-framework/#:~:text=In%20Django%20Rest%20Framework%2C%20the%20detail%20argument%20in,or%20to%20the%20entire%20resource%20collection%20%28list%20view%29.
    """

    @action(methods=['patch'], detail=True)
    def add_member(self, request: Request, pk: int) -> Response:
        deserialized = GroupSerializer(data=request.data, partial=True)
        if not deserialized.is_valid():
            return Response(data=deserialized.errors, status=status.HTTP_400_BAD_REQUEST)
        group = self.get_object()  # returns the resource obj identified by the lookup field 'pk'
        members = deserialized.validated_data.get('members', [])
        # users = [get_object_or_404(User, pk=user_id) for user_id in members]
        # group.members.add(*users)  # Adding multiple users
        group.members.add(*members)
        group.save()
        return Response(data=GroupSerializer(group).data, status=status.HTTP_200_OK)

    @action(methods=['put'], detail=True)
    def update_name(self, request: Request, pk: int) -> Response:
        deserialized = GroupSerializer(data=request.data)
        if not deserialized.is_valid():
            return Response(data=deserialized.errors, status=status.HTTP_400_BAD_REQUEST)
        group = self.get_object()  # group instance identified by 'pk'
        group.name = deserialized.validated_data['name']
        group.save()
        return Response(data=GroupSerializer(group).data, status=status.HTTP_200_OK)

    @action(methods=['delete'], detail=True)
    def remove_member(self, request: Request, pk: int) -> Response:
        print(':: LOG :: GroupViewSet | remove_member is called ...')
        deserialized = self.get_serializer(data=request.data, partial=True)
        if not deserialized.is_valid():
            return Response(data=deserialized.errors, status=status.HTTP_400_BAD_REQUEST)
        instance = self.get_object()
        users = deserialized.validated_data.get('members', [])
        instance.members.remove(*users)  # breaking the association with the group
        return Response(data={
            'removed_members': [user.id for user in users],
            'group': self.get_serializer(instance).data
        }, status=status.HTTP_200_OK)

    # Overridden
    def get_permissions(self):
        if self.action == 'retrieve':
            permission_classes = [HasGroupAccess]
        else:
            permission_classes = GroupViewSet.permission_classes
        return [permission() for permission in permission_classes]


class ListCreateGroupExpenseViewSet(ModelViewSet):
    queryset = GroupExpense.objects.all()
    serializer_class = GroupExpenseSerializer
    permission_classes = [IsGroupAdminOrMember]

    """
    LEARNING:
    - The view obj (self) has access to both 'request' and 'group_id' owing to the below attributes it posses:
      -- self.request
      -- self.kwargs['group_id']
    
    Ref: Stackoverflow: Django REST Framework viewset per-action permissions
    - https://stackoverflow.com/questions/19313314/django-rest-framework-viewset-per-action-permissions
    
    Ref: Object level permissions
    - https://www.django-rest-framework.org/api-guide/permissions/#:~:text=If%20you%27re%20writing%20your%20own%20views%20and%20want,the%20point%20at%20which%20you%27ve%20retrieved%20the%20object.
    
    """

    # Overridden
    def create(self, request: Request, group_id: int) -> Response:
        print(':: LOG :: GroupExpenseViewSet | create :: group_id:', self.kwargs['group_id'])
        deserialized = self.serializer_class(data=request.data)
        if not deserialized.is_valid():
            return Response(data=deserialized.errors, status=status.HTTP_400_BAD_REQUEST)
        # Passing additional data to the save: they will become part of the validated_data (check BaseSerializer)
        group_expense = deserialized.save(created_by=request.user, group=get_object_or_404(Group, pk=group_id))
        return Response(data=GroupExpenseSerializer(group_expense).data, status=status.HTTP_201_CREATED)

    # Overridden
    def perform_create(self, serializer):  # *** IS NOT BEING EXECUTED BECAUSE WE HAVE OVERRIDDEN serializer.create()
        print(':: LOG :: GroupExpenseViewSet :: perform_create')
        group_id = self.kwargs['group_id']
        group = get_object_or_404(Group, pk=group_id)
        print('group_id:', group.id)
        print(':: LOG :: END')
        serializer.save(created_by=self.request.user, group=group)

    # Overridden
    def list(self, request, group_id: int) -> Response:
        queryset = self.queryset.filter(group_id=group_id)
        return Response(data=GroupExpenseSerializer(queryset, many=True).data, status=status.HTTP_200_OK)


class RetrieveUpdateDestroyGroupExpenseViewSet(ModelViewSet):
    queryset = GroupExpense.objects.all()
    serializer_class = GroupExpenseSerializer

    # permission_classes = [IsGroupAdminOrMember]

    # Overridden
    def retrieve(self, request, group_id: int, pk: int) -> Response:
        # ** NOTE: filter() is expected to yield multiple records and hence use 'many=True' in the serializer
        # .filter(group_id=group_id, pk=pk)  # many=True
        group_expense = get_object_or_404(self.get_queryset(), group_id=group_id, pk=pk)
        return Response(data=self.get_serializer(group_expense, many=False).data, status=status.HTTP_200_OK)

    """
    LEARNING:
    - django.core.exceptions.ImproperlyConfigured: Cannot use the @action decorator on the following methods,
    as they are existing routes: destroy
    """

    # ** NOT ALLOWED: existing route
    # @action(methods=['delete'], detail=True, permission_classes=[IsGroupAdminOrMember])
    # Overridden
    def destroy(self, request, group_id: int, pk: int) -> Response:
        pass

    """
    *** ISSUE:
    - Permission class specified in the @action decorator is not being checked
    - Stackoverflow:
      -- https://stackoverflow.com/questions/60114466/django-drf-permission-classes-not-working/78998672#78998672
    
    READ MORE:
    - ViewSets:
      - https://www.django-rest-framework.org/api-guide/viewsets/
    
    """

    # @action decorator is currently dormant
    # @action(methods=['delete'], detail=True, permission_classes=[IsAuthenticated])
    def del_expense(self, request: Request, group_id: int, pk: int) -> Response:
        print(':: LOG :: RetrieveUpdateDestroyGroupExpenseViewSet | del_expense ::')
        # group_expense = get_object_or_404(self.get_queryset(), group_id=group_id, pk=pk)
        # print(':: self.get_object():', self.get_object())  # Uses default lookup field 'pk' to get the target object
        # *** NOTE: calling self.get_object() will automatically trigger the permission class (if any) for object access
        # - The permission class must override 'has_object_permission()'
        group_expense = self.get_object()
        group_expense.delete()  # *** CAUSES DB INTEGRITY ISSUE: Unable to handle deletion of related objects
        return Response(data={'deleted': True, 'group_expense': self.get_serializer(group_expense).data},
                        status=status.HTTP_200_OK)

    """
    LEARNING:
    - Q. How to handle delete for a Model having ManyToMany relations in Django?
      -- https://sl.bing.net/kaNLjcrqhGu
    
    """

    def del_exp_related(self, request: Request, group_id: int, pk: int) -> Response:
        instance = self.get_object()  # will return the target obj if the user has the required permissions
        self.perform_destroy(instance)
        # NOTE: Using ExpenseSerializer because the instance is now deleted and does not point to any group
        return Response(data={'deleted': True, 'group_expense': ExpenseSerializer(instance).data},
                        status=status.HTTP_200_OK)

    # Overridden
    def perform_destroy(self, instance):
        # Deleting all the ManyToMany related fields associated with the group expense
        paid_by = instance.paid_by.all()
        for expense_paid_by in paid_by:
            expense_paid_by.delete()
        shared_by = instance.shared_by.all()
        for expense_shared_by in shared_by:
            expense_shared_by.delete()
        # finally deleting the target
        instance.delete()

    # Overridden
    def get_permissions(self):
        if self.action == 'del_exp_related':  # 'del_expense':
            permission_classes = [IsGroupAdminOrMember, IsGroupAdminOrExpenseCreator]
        else:
            permission_classes = [IsGroupAdminOrMember]
        return [permission() for permission in permission_classes]


class ProfileViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    # Overridden
    def get_queryset(self):
        queryset = super().get_queryset()  # Ensuring queryset is refreshed; read doc str
        return queryset.filter(id=self.request.user.id)

    # Overridden
    def get_object(self):
        return self.get_queryset().first()


class QueryExpenseViewSet(ViewSet):
    permission_classes = [IsAuthenticated]

    def query_user_expense(self, user: User):
        return UserExpense.objects.filter(Q(paid_by=user) | Q(paid_to=user))

    def query_group_expense_paid_by(self, user: User):
        return ExpensePaidBy.objects.filter(user=user)

    def query_group_expense_shared_by(self, user: User):
        return ExpenseSharedBy.objects.filter(user=user)

    def get_user_expense(self, user: User):
        queryset = self.query_user_expense(user).order_by('created_at')
        serialized = QueryUserExpenseSerializer(queryset, many=True, context={'requested_by': user})
        return serialized.data

    def get_group_expense(self, user: User):
        queryset_1 = self.query_group_expense_paid_by(user).order_by('group_expense__created_at')
        serialized_1 = QueryGroupExpenseSerializer(queryset_1, many=True, context={'is_owed': False})
        queryset_2 = self.query_group_expense_shared_by(user).order_by('group_expense__created_at')
        serialized_2 = QueryGroupExpenseSerializer(queryset_2, many=True, context={'is_owed': True})
        return serialized_1.data + serialized_2.data

    @action(methods=['get'], detail=False)
    def get_expense(self, request: Request):
        query = (request.query_params.get('query', 'all')).strip().lower()
        query_type = Query(query)
        if query_type == Query.USER_EXPENSE:
            expense_data = self.get_user_expense(request.user)
        elif query_type == Query.GROUP_EXPENSE:
            expense_data = self.get_group_expense(request.user)
        else:
            expense_data = self.get_user_expense(request.user) + self.get_group_expense(request.user)
        expense_data.sort(key=lambda data: data['created_at'], reverse=True)
        return Response(data=expense_data, status=status.HTTP_200_OK)

    def get_owed(self, request: Request):
        pass


class GroupSettleUpViewSet(ViewSet):
    permission_classes = [IsGroupAdminOrMember]

    def settle_up(self, request: Request, group_id: int) -> Response:
        fields = ['user', 'expense_amount']
        queryset_paid = (ExpensePaidBy.objects.filter(group_expense__group__id=group_id)
                         .annotate(expense_amount=F('amount'))
                         .values_list(*fields))
        queryset_shared = (ExpenseSharedBy.objects.filter(group_expense__group__id=group_id)
                           .annotate(expense_amount=-F('amount'))  # -ve sign indicates owed amount
                           .values_list(*fields))
        balance_sheet = build_balance_sheet(*queryset_paid, *queryset_shared)
        # print(':: LOG :: GroupSettleUpViewSet | settle_up ::')
        # print(':: balance_sheet ::', balance_sheet)
        query_strategy = request.query_params.get('strategy', SettlementType.N_MINUS_1.value)
        settlement_strategy = SettlementStrategyFactory.get_by_name(query_strategy)
        transactions = settlement_strategy.settle_up(balance_sheet)
        return Response(data=[transaction.to_dict() for transaction in transactions], status=status.HTTP_200_OK)


"""
LEARNINGS:

Q. How to create a custom column in QuerySet in DRF?
- https://www.bing.com/search?q=How+to+create+a+custom+column+in+QuerySet+in+DRF&qs=n&form=QBRE&sp=-1&ghc=1&lq=0&pq=how+to+create+a+custom+column+in+queryset+in+dr&sc=0-47&sk=&cvid=DF8CDD997C9D4D7381E092F9392BC245&ghsh=0&ghacc=0&ghpl=

Passing context to the serializer while serializing queryset
- https://sl.bing.net/hzT3Pyini56

Combining QuerySet from two different base models
- https://www.bing.com/search?pglt=163&q=How+to+combine+results+from+two+different+base+models+in+DRF&cvid=79f10d0898e849299d2846ebbe58470e&gs_lcrp=EgZjaHJvbWUyBggAEEUYOdIBCDcxMDNqMGoxqAIAsAIA&FORM=ANNTA1&PC=U531

Q. How to make querysets returned from two different base models compatible for union?
- https://www.bing.com/search?q=How+to+make+querysets+returned+from+two+different+base+models+compatible+for+union&qs=n&form=QBRE&sp=-1&ghc=1&lq=1&pq=how+to+make+querysets+returned+from+two+different+base+models+compatible+for+union&sc=1-82&sk=&cvid=E445EAB5C0664D1A97757B12BEC39728&ghsh=0&ghacc=0&ghpl=&showconv=0
- https://docs.djangoproject.com/en/5.1/ref/models/querysets/#union

Serializing 'values_list' in Django
- https://sl.bing.net/eR1oAIpEHYG

Q object in Django
- https://www.bing.com/search?pglt=163&q=Q+in+Django&cvid=d363b05d76c04777ba26a628f1f7fd65&gs_lcrp=EgZjaHJvbWUyBggAEEUYOTIGCAEQABhAMgYIAhAAGEAyBggDEAAYQDIGCAQQABhAMgYIBRAAGEAyBggGEAAYQDIGCAcQRRg8MgYICBBFGDzSAQg2MjQ5ajBqMagCCLACAQ&FORM=ANNTA1&PC=U531
- https://www.scaler.com/topics/django/q-objects-and-f-objects/

"""
