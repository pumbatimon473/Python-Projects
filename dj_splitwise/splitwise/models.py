from django.db import models
from django.contrib.auth.models import AbstractUser


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class User(AbstractUser):
    # expense_groups: m : m relation
    # paid: 1 : m relation
    # owe: 1 : m relation
    pass


class Expense(BaseModel):
    amount = models.DecimalField(max_digits=7, decimal_places=2)
    title = models.CharField(max_length=32)
    description = models.CharField(max_length=128)
    created_by = models.ForeignKey(User, on_delete=models.DO_NOTHING,
                                   related_name='created_expenses')


class UserExpense(Expense):
    paid_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='paid')
    paid_to = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='owe')


class Group(BaseModel):
    name = models.CharField(max_length=32)
    members = models.ManyToManyField(User, related_name='expense_groups')
    # expenses: 1 : m relation
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='created_groups', null=True)


class ExpensePaidBy(BaseModel):
    amount = models.DecimalField(max_digits=7, decimal_places=2)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)


class ExpenseSharedBy(BaseModel):
    amount = models.DecimalField(max_digits=7, decimal_places=2)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)


"""
Difference between ManyToManyField and ManyToManyRel:
- Use ManyToManyField to specify the relation
  -- ManyToManyRel is used internally by Django to implement the ManyToManyField relation

- Ref: Stackoverflow
  -- https://stackoverflow.com/questions/67158034/difference-between-djangos-manytomanyfield-and-manytomanyrel
- Ref: Doc
  -- https://docs.djangoproject.com/en/5.1/topics/db/examples/many_to_many/

"""


class GroupExpense(Expense):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='expenses')
    paid_by = models.ManyToManyField(ExpensePaidBy, related_name='group_expense')
    shared_by = models.ManyToManyField(ExpenseSharedBy, related_name='group_expense')
