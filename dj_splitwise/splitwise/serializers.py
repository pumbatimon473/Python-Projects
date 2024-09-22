from rest_framework import serializers
from .models import User, UserExpense, Expense, Group, GroupExpense
from .models import ExpensePaidBy, ExpenseSharedBy
import functools
from rest_framework.exceptions import ValidationError
from typing import List
from collections import OrderedDict


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'
        extra_kwargs = {
            'password': {'write_only': True}
        }

    # Overridden
    def create(self, validated_data) -> User:
        user = User.objects.create(**validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user

    # Overridden
    def to_representation(self, instance):
        instance_dict = super().to_representation(instance)
        # returning only the non-empty attributes
        return OrderedDict(filter(lambda attr_val_pair: True if attr_val_pair[1] else False, instance_dict.items()))


class UserExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserExpense
        fields = '__all__'
        read_only_fields = ['paid_by', 'created_by']


class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = '__all__'


"""
Serializer relations:

Ref: DOC
- https://www.django-rest-framework.org/api-guide/relations/
  -- Album, Track models example
    --- 'unique_together' attribute in serializer Meta class
"""


class GroupSerializer(serializers.ModelSerializer):
    # ** NOTE: 'members' is a ManyToMany related field
    # Option 1: serialize the related field as a list of nested obj
    # members = UserSerializer(many=True, required=False)  # Using the target obj serializer
    # Option 2: serialize the related field as a list of primary keys
    members = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all(), required=False)

    class Meta:
        model = Group
        fields = '__all__'
        # read_only_fields = ['members']


class ExpensePaidBySerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=True)

    class Meta:
        model = ExpensePaidBy
        fields = '__all__'


class ExpenseSharedBySerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=True)

    class Meta:
        model = ExpenseSharedBy
        fields = '__all__'


class GroupExpenseSerializer(serializers.ModelSerializer):
    paid_by = ExpensePaidBySerializer(many=True, required=True)  # Nested Serializer
    shared_by = ExpenseSharedBySerializer(many=True, required=True)  # Nested Serializer

    class Meta:
        model = GroupExpense
        fields = '__all__'
        read_only_fields = ['created_by', 'group']  # Taken care by Auth
        unique_together = ['group', 'id']

    def is_valid_expense(self, validated_data: dict):
        """

        :param validated_data: A dict representing the expense data
        :return: True if the expense amount is eq to the total amount paid and total amount shared
        """
        expense_amt = validated_data.get('amount', 0)
        total_amt_paid = functools.reduce(lambda _sum, paid: _sum + paid.get('amount', 0),
                                          validated_data.get('paid_by'), 0)
        total_amt_shared = functools.reduce(lambda _sum, shared: _sum + shared.get('amount', 0),
                                            validated_data.get('shared_by'), 0)
        print(':: LOG :: GroupExpenseSerializer :: is_valid_expense()')
        print('Expense Amount:', expense_amt)
        print('Total Amount Paid:', total_amt_paid)
        print('Total Amount Shared:', total_amt_shared)
        print(':: LOG :: END')
        return expense_amt == total_amt_paid == total_amt_shared

    def are_all_members(self, group: Group, participant_data: List[dict]):
        for participant in participant_data:
            user = participant['user']
            if not (user.id == group.created_by_id or
                    group.members.filter(pk=user.id).exists()):
                return False
        return True

    """
    Writable Nested Serializer:
    - *** The `.create()` method does not support writable nested fields by default.
      -- Write an explicit `.create()` method for serializer `splitwise.serializers.GroupExpenseSerializer`,
    or set `read_only=True` on nested serializer fields.
    - Ref: https://www.django-rest-framework.org/topics/writable-nested-serializers/#writable-nested-serializers
    
    Create and update Django rest framework nested serializers:
    - Ref: https://django.cowhite.com/blog/create-and-update-django-rest-framework-nested-serializers/
    
    *** NOTE:
    - add(), create(), remove(), clear(), and set() all apply database changes immediately
    for all types of related fields. In other words, there is no need to call save() on either end of the relationship.
    - Ref: https://docs.djangoproject.com/en/2.1/ref/models/relations/#django.db.models.fields.related.RelatedManager.set
    """

    # Overridden
    def create(self, validated_data: dict) -> GroupExpense:
        if not self.is_valid_expense(validated_data):
            raise ValidationError('Expense amount should be equal to the total amount paid and total amount shared')
        group = validated_data['group']
        paid_by_data = validated_data.pop('paid_by')
        shared_by_data = validated_data.pop('shared_by')
        if not self.are_all_members(group, paid_by_data) or not self.are_all_members(group, shared_by_data):
            raise ValidationError('All the participants in the expense must be members of the group')
        group_expense = GroupExpense.objects.create(**validated_data)
        # create all ExpensePaidBy
        for paid_by in paid_by_data:
            # ** Getting below error:
            """
            TypeError:
            Direct assignment to the reverse side of a many-to-many set is prohibited. Use group_expense.set() instead.
            
            My Understanding:
            - The one who is pointing (defined the relation) needs to know the other side
            and hence the other side must be created first.
              -- Here, the other sides are ExpensePaidBy and ExpenseSharedBy
            """
            # ExpensePaidBy.objects.create(group_expense=group_expense, **paid_by)  # TypeError
            group_expense.paid_by.add(ExpensePaidBy.objects.create(**paid_by))  # WORKS
        # create all ExpenseSharedBy
        for shared_by in shared_by_data:
            group_expense.shared_by.add(ExpenseSharedBy.objects.create(**shared_by))
        return group_expense


class QueryUserExpenseSerializer(serializers.Serializer):
    expense_id = serializers.IntegerField(source='id')
    expense_amount = serializers.SerializerMethodField()
    title = serializers.CharField()
    description = serializers.CharField()
    created_at = serializers.DateTimeField()
    created_by = serializers.StringRelatedField(read_only=True)

    # NOTE: serializer is able to automatically map the field to its corresponding method
    # as long as the method name follows the pattern: 'get_<field_name>'
    def get_expense_amount(self, instance):
        user = self.context.get('requested_by')
        if not user:
            raise ValidationError('Missing context! User context is required.')
        if instance.paid_to_id == user.id:
            return -instance.amount
        return instance.amount

    # Overridden
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        expense_amount = representation.get('expense_amount', 0)
        # ensuring expense_amount is a decimal field
        representation['expense_amount'] = (serializers.DecimalField(max_digits=7, decimal_places=2)
                                            .to_representation(expense_amount))
        return representation


class QueryGroupExpenseSerializer(serializers.Serializer):
    expense_id = serializers.IntegerField(source='group_expense.first.id')
    expense_amount = serializers.SerializerMethodField()
    title = serializers.CharField(source='group_expense.first.title')
    description = serializers.CharField(source='group_expense.first.description')
    created_at = serializers.DateTimeField(source='group_expense.first.created_at')
    created_by = serializers.StringRelatedField(source='group_expense.first.created_by')

    def get_expense_amount(self, instance):
        is_owed = self.context.get('is_owed')
        if is_owed is None:
            raise ValidationError('Missing context! Expense type is required.')
        if is_owed:
            return -instance.amount
        return instance.amount

    # Overridden
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # ensuring expense_amount is a decimal field
        expense_amount = representation.get('expense_amount', 0)
        representation['expense_amount'] = (serializers.DecimalField(max_digits=7, decimal_places=2)
                                            .to_representation(expense_amount))
        return representation


# TEST CLASSES
"""
LEARNINGS:

Q. I want to populate value from a ManyToManyField in a CharField serializer in DRF.
- https://sl.bing.net/fNVpviFSAUK

Core arguments in serializer fields - DRF:
- https://www.geeksforgeeks.org/core-arguments-in-serializer-fields-django-rest-framework/

Q. Populating a serializer decimal field sourced from a custom method defined in the serializer itself
- https://sl.bing.net/dhVvfIivkoC

"""
