from django.shortcuts import render, get_object_or_404
from rest_framework import generics, status, response
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from .serializers import UserSerializer, CreateUserSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from accounts.authentication import BearerTokenAuthentication
from accounts.permissions import CustomerAccessPermission


User = get_user_model()

# Create your views here.
class LoginView(generics.CreateAPIView):
    
    def post(self, request, *args, **kwargs):
        
        # TODO:
        # add validation to ensure email and password are provided
        # in the post body
        
        
        user = get_object_or_404(User, email=request.data.get('email'))
        


        # if the user is not active throw error
        if not user.is_active:    
            return response.Response({'detail': 'authentication failed'}, status=status.HTTP_400_BAD_REQUEST)    
        
        # if password does not match 
        if not user.check_password(request.data.get('password')):
            print(request.data.get('password'))
            return response.Response({'detail': 'invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)    
        
        # delete all previous tokens
        Token.objects.filter(user=user).delete()
        
        # create a new token for that user
        token = Token.objects.create(user=user)
        
        data = dict()
        data['user'] = UserSerializer(user).data
        data['token'] = token.key
        
        return response.Response(data, status=status.HTTP_201_CREATED)
    

class LogoutView(generics.CreateAPIView):
    
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        tokens = Token.objects.filter(user=request.user)
        # delete all tokens affiliated with this user
        tokens.delete()
        return response.Response({'detail': 'Logout Successful'}, status=status.HTTP_200_OK)


class ChangePasswordView(generics.CreateAPIView):
    
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        
        # validate that the user sends the old password and new password
        if request.user.check_password(request.data.get('old_password')):
            request.user.set_password(request.data.get('new_password'))
            return response.Response({'detail': 'success'}, status=status.HTTP_200_OK)    
        return response.Response({'detail': 'incorrect password provided'}, status=status.HTTP_400_BAD_REQUEST)
   
    
class ResetPasswordView(generics.CreateAPIView):
    
    
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        
        user = get_object_or_404(User, id=request.data.get("id"))
        
        user.set_password(request.data.get("password"))
        
        return response.Response({
            'detail': 'success'
        },
        status=status.HTTP_200_OK)
    
    
class ListCreateUserView(generics.ListCreateAPIView):
    
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [IsAuthenticated, CustomerAccessPermission]
    
    def get(self, request, *args, **kwargs):
        users = User.objects.all()
        
        if request.query_params.get("first_name"):
            users = users.filter(first_name__icontains=request.query_params.get("first_name"))
        if request.query_params.get("last_name"):
            users = users.filter(last_name__icontains=request.query_params.get("last_name"))
        if request.query_params.get("email"):
            users = users.filter(email__icontains=request.query_params.get("email"))
        if request.query_params.get("is_active"):
            value = True if request.query_params.get("is_active") == 'true' else False
            users = users.filter(is_active=value)
        
        
        user_serializer = UserSerializer(self.paginate_queryset(users), many=True)
        
        return self.paginator.get_paginated_response(user_serializer.data)    
    
    def post(self, request, *args, **kwargs):
        
        data = dict()
        try:
            if User.objects.filter(email=request.data.get("email")):
                return response.Response({
                    "detail": "This email already exists"
                }, status=status.HTTP_400_BAD_REQUEST)
            if User.objects.filter(username=request.data.get("username")):
                return response.Response({
                    "detail": "This username already exists"
                }, status=status.HTTP_400_BAD_REQUEST)
            print(request.data.get("customer_perm"))

            user = User.objects.create(
                is_lead=False,
                first_name=request.data.get('first_name'),
                last_name=request.data.get('last_name'),
                email=request.data.get('email'),
                username=request.data.get('username'),

                phone_no=request.data.get('phone_no'),
                address_1=request.data.get('address_1'),
                address_2=request.data.get('address_2'),
                city=request.data.get('city'),
                state=request.data.get('state'),
                zip=request.data.get('zip'),
                country=request.data.get('country'),

                customer_perm=request.data.get('customer_perm'),
                items_perm=request.data.get('items_perm'),
                item_kits_perm=request.data.get('item_kits_perm'),
                suppliers_perm=request.data.get('suppliers_perm'),
                reports_perm=request.data.get('reports_perm'),
                receivings_perm=request.data.get('receivings_perm'),
                sales_perm=request.data.get('sales_perm'),
                employees_perm=request.data.get('employees_perm'),
            )

            user.set_password(request.data.get("password"))
            user.save()
            user = CreateUserSerializer(user).data

            data['detail'] = user
            
            return response.Response(
                data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return response.Response(
                {
                    "detail": "Oops! something went wrong, please contact the admin",
                },
                status=status.HTTP_400_BAD_REQUEST
            )


    
class ActivateUserView(generics.CreateAPIView):
    
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        
        # :TODO
        # validate to ensure that ids have been passed in the json payload
        
        users = User.objects.filter(id__in=request.data.get("ids"))
        for user in users:
            user.is_active = True
            user.save()
            
        return response.Response({'detail': 'success'}, status=status.HTTP_200_OK)
    

class UpdateUserView(generics.CreateAPIView):
    
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [IsAuthenticated, CustomerAccessPermission]
    
    def post(self, request, *args, **kwargs):
        print(request.user)
        user = get_object_or_404(User, username=request.data.get("user_data")['username'])
        user_serializer = UserSerializer(user)

        serializer = UserSerializer(user, data=request.data.get("user_data"), partial=True)
        if serializer.is_valid(raise_exception=False):
            serializer.save()

            #update password if password is contained in the request
            if request.data.get("user_password")['password']:
                print('shouldnt get to here')
                user.set_password(request.data.get("user_password")['password'])
                user.save()

            return response.Response({
                "detail": serializer.data
            }, status=status.HTTP_200_OK)
        return response.Response(
            {
                "error": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class DeactivateUserView(generics.CreateAPIView):
    
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        
        # :TODO
        # validate to ensure that ids have been passed in the json payload
        
        users = User.objects.filter(id__in=request.data.get("ids"))
        
        for user in users:
            user.is_active = False
            user.save()

        return response.Response({'detail': 'success'}, status=status.HTTP_200_OK)
    

class DeleteUserView(generics.CreateAPIView):
    
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        
        # :TODO
        # validate to ensure that ids have been passed in the json payload
        
        users = User.objects.filter(id__in=request.data.get("ids"))
        users.delete()
        
        return response.Response({'detail': 'success'}, status=status.HTTP_200_OK)
    
class DeleteOneUserView(generics.CreateAPIView):
    
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        print(request.data.get("username"))
        
        user = get_object_or_404(User, username=request.data.get("username"))
        user.delete()
        
        return response.Response({'detail': 'success'}, status=status.HTTP_200_OK)

    
class ProfileView(generics.ListCreateAPIView):
    
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        user_department = request.user.dept
        same_dept = User.objects.all().filter(dept=user_department)
        
        data = dict()
        
        user = UserSerializer(request.user).data
        same_dept_users = UserSerializer(same_dept, many=True).data    
        return response.Response({'detail': user, 'others': same_dept_users}, status=status.HTTP_200_OK)
    
    
    