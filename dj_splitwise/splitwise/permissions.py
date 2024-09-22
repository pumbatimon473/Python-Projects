from rest_framework.permissions import BasePermission
from django.shortcuts import get_object_or_404
from .models import Group, User
from django.db.models.query import QuerySet
from rest_framework.exceptions import PermissionDenied
from django.http.response import Http404
from .models import GroupExpense

"""
Authentication & Permissions:
- https://www.django-rest-framework.org/tutorial/4-authentication-and-permissions/

How to restrict profile access only to the logged in user?
- https://www.bing.com/search?pglt=163&q=How+to+restrict+profile+access+only+to+the+logged+in+user+in+DRF&cvid=18a643e196b944dca5d0567caa6930dc&gs_lcrp=EgZjaHJvbWUyBggAEEUYOdIBCjE0OTg2M2owajGoAgiwAgE&FORM=ANNTA1&PC=LCTS

"""


class IsOwner(BasePermission):
    # Overridden
    def has_object_permission(self, request, view, obj):
        print(':: LOG :: IsOwner | has_object_permission() called ...')
        return request.user.id == obj.id


class IsGroupAdmin(BasePermission):
    # Overridden
    def has_object_permission(self, request, view, obj):
        return request.user.id == obj.created_by.id


class IsGroupAdminOrMember(BasePermission):
    """
    LEARNING:
    - For related fields in the model obj, we get their corresponding manager
      -- e.g.,
      Group:
        - expenses: 1 : m
        - members: m : m

      group = get_object_or_404(Group, pk=group_id)  # returns model obj of the Group
      group.expenses: is a 'RelatedManager'
      group.members: is a 'ManyRelatedManager'

      NOTE: The default manger we have been using so far is 'objects' over Model class

    - Read doc for 'get_object_or_404()':
      -- klass could be a Model, Manager or QuerySet object
    """

    # Overridden
    def has_permission(self, request, view):
        print(':: LOG :: IsGroupAdminOrMember ::')
        group_id = view.kwargs['group_id']
        print('group_id:', group_id)
        group = get_object_or_404(Group, pk=group_id)
        print('group.members:', group.members, '|', type(group.members))
        queryset: QuerySet[User] = group.members.all()
        print('group.members.all():', queryset)
        # member = get_object_or_404(group.members, pk=request.user.id)
        # print('access requested by group.member:', member)
        print(':: LOG :: END')
        try:
            return request.user.id == group.created_by.id or get_object_or_404(group.members, pk=request.user.id)
        except Http404 as e:
            raise PermissionDenied(f'The User does not have the required permissions to perform this action.')


class IsGroupAdminOrExpenseCreator(BasePermission):
    # Overridden
    def has_object_permission(self, request, view, obj: GroupExpense):
        """
        :param obj: Refers to the GroupExpense obj
        """
        print(':: LOG :: IsGroupAdminOrExpenseCreator | has_object_permission() called ...')
        group_id = view.kwargs['group_id']
        group = get_object_or_404(Group, pk=group_id)
        # Ensuring the expense obj is associated with the given group_id
        return obj.group.id == group_id and \
            (request.user.id == group.created_by.id or request.user.id == obj.created_by.id)


class HasGroupAccess(BasePermission):
    def has_object_permission(self, request, view, obj: Group):
        return request.user.id == obj.created_by_id or obj.members.filter(pk=request.user.id).exists()