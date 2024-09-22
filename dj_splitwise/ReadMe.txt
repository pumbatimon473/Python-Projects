Splitwise:
- Schema_v2


Exposed Endpoints:
- Token:
  -- api/token/
    --- POST: to obtain the access and refresh tokens
  -- api/token/refresh/
    --- POST: to obtain the refresh token

- User:
  -- register/user/
    --- POST: to register a new user
  -- profile/
    --- required permissions: IsOwner
    --- GET: returns the user's profile details
    --- PATCH: allows the user to update his/her profile

- UserExpense:
  -- expense/user/
    --- required permissions: IsAuthenticated
    --- POST: creates a new UserExpense
      ---- NOTE: Assumption: The logged-in user is considered to be the creator as well as the person who
      paid for the expense. We just have to specify the other user (only 1) participating in the expense.

- Group:
  -- user/group/
    --- required permissions: IsAuthenticated
    --- POST: creates an expense group
  -- user/group/<int:pk>/
    --- required permissions: HasGroupAccess
      ---- GET: retrieves the details about the group
    --- required permissions: IsGroupAdmin
      ---- PATCH: adds member(s) to the group
      ---- PUT: changes the name of the group
      ---- DELETE: removes member(s) from the group

- GroupExpense:
  -- expense/group/<int:group_id>/
    --- required permissions: IsGroupAdminOrMember
    --- POST: creates a new group expense
    --- GET: retrieves all the expenses in the group
  -- expense/group/<int:group_id>/id/<int:pk>/
    --- required permissions: IsGroupAdminOrMember
      ---- GET: retrieves group expense by id
    --- required permissions: IsGroupAdminOrMember, IsGroupAdminOrExpenseCreator
      ---- DELETE: deletes group expense by id

- QueryExpense:
  -- user/expense/
    --- required permissions: IsAuthenticated
      ---- GET: retrieves all the expenses, the user is involved in
        ----- Query Param: query = all | user_expense | group_expense
        ----- Returns the expenses ordered by creation date and time, latest first

- SettleUp:
  -- expense/group/<int:group_id>/settle_up/
    --- required permissions: IsGroupAdminOrMember
      ---- GET: retrieves the list of transactions for the group settlement
        ----- Query Param: strategy = n_minus_1 | greedy


Admin:
  -- admins/user/
    --- required permissions: IsAdminUser
    --- GET: returns the details of all the users
  -- admins/user/<int:pk>/
    --- required permissions: IsAdminUser
    --- Allowed methods: GET, PUT, PATCH, DELETE
  -- admins/expense/
    --- required permissions: IsAdminUser
    --- GET: returns a list of all the expenses
  -- admins/expense/user/
    --- required permissions: IsAdminUser
    --- GET: returns a list of all the user expenses


Fulfilled Requirements:
- 1. Users should be able to register and update their profiles.
  -- A user's profile consists of username, email, password, first_name, last_name
- 2. Users can participate in expenses with other users
  -- NOTE: The creator of the expense is considered to be the person who paid for the expense.
  The other person owes the money.
- 3. A user should be able to create a group to manage the expenses involving other users
  -- NOTE: The creator of the group is considered the group admin and is implicit member of the group
- 4. Only the group admin should be able to add/remove members from the group
  -- NOTE: A group admin cannot remove himself/herself from the group
- 5. Only the group admin or its members should be able to create expenses under that group
- 6. Only the group admin or its members can view the list of expenses under that group
- 7. A group expense can be deleted only by the group admin or the creator of the expense
as long as the creator is part of that group
- 8. A user can see a history of expenses, he/she involved in
- 9. A user is able to request for group settlement he/she participating in
