from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import json
from django.contrib.auth import authenticate
from .models import CustomUser
from tenant.models import Tenant, InviteCode
from django.contrib.auth import logout
from django.db import connections
from django.db import connection, IntegrityError
import logging
from django.shortcuts import get_object_or_404
logger = logging.getLogger(__name__)
import json
import uuid
import secrets
from django.http import JsonResponse
from django.db import IntegrityError, transaction
from django.contrib.auth import get_user_model
import os
def generate_symmetric_key():
    return os.urandom(32)   # ✅ bytes



CustomUser = get_user_model()
@csrf_exempt
def register_tenant(request):
    if request.method != 'POST':
        return JsonResponse({'msg': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)

        email = data.get('email')
        phone = data.get('phone')
        password = data.get('password')

        if not password or not (email or phone):
            return JsonResponse(
                {'msg': 'Email or phone and password are required'},
                status=400
            )

        # Prevent duplicate users
        if email and CustomUser.objects.filter(email=email).exists():
            return JsonResponse({'msg': 'Email already registered'}, status=400)

        if phone and CustomUser.objects.filter(phone_number=phone).exists():
            return JsonResponse({'msg': 'Phone already registered'}, status=400)

        # Generate tenant data
        tenant_id = uuid.uuid4().hex[:12]
        organization = f"org_{tenant_id}"
        db_password = secrets.token_urlsafe(16)
        key = generate_symmetric_key()

        with transaction.atomic():
            # Create Tenant
            tenant = Tenant.objects.create(
                id=tenant_id,
                organization=organization,
                db_user=f"crm_tenant_{tenant_id}",
                db_user_password=db_password,
                key=key
            )

            # Create Admin User
            user = CustomUser.objects.create_user(
                username=email or phone,
                email=email,
                phone_number=phone,
                password=password,
                role=CustomUser.ADMIN,
                organization=organization,
                tenant=tenant
            )

            # Create PostgreSQL role
           
        return JsonResponse({
            'msg': 'Tenant and admin user created successfully',
            'tenant_id': tenant_id,
            'organization': organization
        })

    except IntegrityError as e:
        return JsonResponse({'msg': str(e)}, status=500)
    except Exception as e:
        return JsonResponse({'msg': str(e)}, status=500)


@csrf_exempt
def register(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data.get('username')
        email = data.get('email')
        phone = data.get('phone')
        password = data.get('password')
        # role = data.get('role', CustomUser.EMPLOYEE)  # Default role to employee if not provided
        organization = data.get('organisation')
        tenant_name = data.get('tenant')
        role = CustomUser.ADMIN
        
        if not username:
            print("Missing field: username")
        if not email:
            print("Missing field: email")
        if not phone:
            print("Missing field: phone")
        if not password:
            print("Missing field: password")
        if not organization:
            print("Missing field: organisation")
        if not tenant_name:
            print("Missing field: tenant_name")
    
        if not (username and email and password and organization and tenant_name and phone):
            print("One or more required fields are missing")
            return JsonResponse({'msg': 'Missing required fields'}, status=400)
        
        if CustomUser.objects.filter(username=username).exists():
            return JsonResponse({'msg': 'Username already exists'}, status=400)
        
        try:
            tenant = Tenant.objects.get(id=tenant_name)
        except Tenant.DoesNotExist:
            return JsonResponse({'msg': 'Specified tenant does not exist'}, status=400)
        
        # Create a new user with the specified role, organization, and tenant
        user = CustomUser.objects.create_user(username=username, email=email, password=password, role=role, organization=organization, tenant=tenant, phone_number = phone)

        # Create a corresponding PostgreSQL role for the userx``
        try:
            with connection.cursor() as cursor:
                
                sql_role_name = f"crm_tenant_{role}"
                
                cursor.execute(f"CREATE ROLE {username} WITH LOGIN PASSWORD %s IN ROLE {sql_role_name};", [password])
                cursor.execute(f"GRANT {sql_role_name} TO {username};")
                
        except IntegrityError as e:
            return JsonResponse({'msg': f'Error creating role: {str(e)}'}, status=500)
        except Exception as e:
            return JsonResponse({'msg': f'Unexpected error: {str(e)}'}, status=500)

        return JsonResponse({'msg': 'User registered successfully'})
    else:
        return JsonResponse({'msg': 'Method not allowed'}, status=405)


from .models import CustomUser
@csrf_exempt
def change_password(request):
    if request.method == 'POST':
        print("req: ", request)
        data = json.loads(request.body)
        print(data)
        username = data.get('username')
        new_password = data.get('newPassword')
        phone = data.get('phone')
        print(username, new_password)
        try:
            # Retrieve the user by username
            u = CustomUser.objects.get(username = username)
            print(u)
            if new_password:
                u.set_password(new_password)
                u.save()
                return JsonResponse({'message': 'Password changed successfully'}, status=200)
            elif phone:
                if phone == u.phone_number:
                    return JsonResponse({} ,status = 200)
                else:
                    return JsonResponse({'message': 'Please enter registered phone number'}, status = 500)
        except CustomUser.DoesNotExist:
            return JsonResponse({'error': 'User does not exist'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@csrf_exempt
def verifyUser(request):
    if request.method == 'POST':
        print("req: ", request)
        data = json.loads(request.body)
        print(data)
        username = data.get('username')
        phone = data.get('phone')
        print(username, phone)


import jwt
import datetime
from django.conf import settings

class LoginView(APIView):
    def post(self, request):
        try:
            data = request.data
            username = data.get('username')
            password = data.get('password')

            if not (username and password):
                return Response({'msg': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)

            user = authenticate(username=username, password=password)
            print("user logged in is", user)

            if user:
                tenant_id = user.tenant.id  # Get tenant ID
                user_id = user.id
                role = user.role

                # Fetch tenant tier
                try:
                    tenant_obj = Tenant.objects.get(id=tenant_id)
                    tier = tenant_obj.tier if hasattr(tenant_obj, 'tier') else 'free'
                except Tenant.DoesNotExist:
                    tier = 'free'

                now = datetime.datetime.utcnow()

                # Generate JWT access token
                access_payload = {
                    "sub": str(user_id),
                    "tenant_id": str(tenant_id),
                    "tier": tier,
                    "role": role,
                    "scope": "user",
                    "iat": now,
                    "exp": now + datetime.timedelta(seconds=settings.JWT_ACCESS_TOKEN_LIFETIME),
                }

                # Generate JWT refresh token
                refresh_payload = {
                    "sub": str(user_id),
                    "tenant_id": str(tenant_id),
                    "tier": tier,
                    "role": role,
                    "type": "refresh",
                    "iat": now,
                    "exp": now + datetime.timedelta(seconds=settings.JWT_REFRESH_TOKEN_LIFETIME),
                }

                access_token = jwt.encode(
                    access_payload,
                    settings.JWT_SECRET,
                    algorithm=settings.JWT_ALGORITHM,
                )
                refresh_token = jwt.encode(
                    refresh_payload,
                    settings.JWT_SECRET,
                    algorithm=settings.JWT_ALGORITHM,
                )

                response_data = {
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'token_type': 'Bearer',
                    'expires_in': settings.JWT_ACCESS_TOKEN_LIFETIME,
                    'tenant_id': tenant_id,
                    'user_id': user_id,
                    'role': role,
                    'tier': tier,
                    'msg': 'Login successful'
                }
                print("user data", response_data)
                return Response(response_data, status=status.HTTP_200_OK)
            else:
                logger.error(f"Authentication failed for username: {username}")
                return Response({'msg': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        except Exception as e:
            logger.error(f"Login error for {request.data.get('username', 'unknown')}: {str(e)}")
            return Response({'msg': f'Login failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class LogoutView(APIView):
    def post(self, request):
        # Log out Django user session
        logout(request)
        
        tenant_id = request.headers.get('X-Tenant-Id')
        print("Logging out tenant:", tenant_id)

        try:
            connection = connections['default']
            cursor = connection.cursor()
            # Clear tenant session variable
            cursor.execute("RESET my.tenant_id")
            cursor.close()
            # Close connection to clear session state
            connection.close()
            logger.debug("Cleared tenant session variable and closed DB connection on logout")
        except Exception as e:
            logger.error(f"Error clearing tenant session variable on logout: {e}")

        return Response({'msg': 'Logout successful'}, status=200)

# class LogoutView(APIView):
#     def post(self, request):
#         # Log out the user
#         logout(request)
#         tenant_id = request.headers.get('X-Tenant-Id')
#         print("logging out tenant ", tenant_id)
#         # Reset the database connection to default superuser
#         connection = connections['default']
#         connection.settings_dict.update({
#             'USER': 'nurenai',
#             'PASSWORD': 'Biz1nurenWar*',
#         })
#         connection.close()
#         connection.connect()
#         logger.debug("Database connection reset to default superuser")
        
#         return Response({'msg': 'Logout successful'}, status=status.HTTP_200_OK)

# class LoginView(APIView):
#     def post(self, request):
#         data = request.data
#         username = data.get('username')
#         password = data.get('password')
        
#         if not (username and password):
#             return Response({'msg': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)
        
#         # Authenticate user
#         user = authenticate(username=username, password=password)
#         print("user logged in is", user)
#         if user:
#             # Check user's role and tenant
#             role = user.role
#             tenant_id = user.tenant.id  # Get the tenant ID associated with the user
#             user_id = user.id  # Get the user ID of the logged-in user

#             response_data = {
#                 'tenant_id': tenant_id,
#                 'user_id': user_id,
#                 'role': role
#             }
#             print("response data: " , response_data)
#             if role == CustomUser.ADMIN:
#                 # Show admin views
#                 response_data['msg'] = 'Login successful as admin'
#             elif role == CustomUser.MANAGER:
#                 # Show manager views
#                 response_data['msg'] = 'Login successful as manager'
#             else:
#                 # Show employee views
#                 response_data['msg'] = 'Login successful as employee'
            
#             return Response(response_data, status=status.HTTP_200_OK)
#         else:
#             logger.error(f"Authentication failed for username: {username}")
#             return Response({'msg': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


# ──────────────────────────────────────────────
# Unified Registration (Create Org / Join Org)
# ──────────────────────────────────────────────

@csrf_exempt
def register_unified(request):
    if request.method != 'POST':
        return JsonResponse({'msg': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        mode = data.get('mode')  # "create" or "join"
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        phone = data.get('phone', '').strip()

        # Validate common required fields
        if not username or not email or not password:
            return JsonResponse({'msg': 'Username, email, and password are required'}, status=400)

        if mode not in ('create', 'join'):
            return JsonResponse({'msg': 'Mode must be "create" or "join"'}, status=400)

        if CustomUser.objects.filter(username=username).exists():
            return JsonResponse({'msg': 'Username already exists'}, status=400)

        if CustomUser.objects.filter(email=email).exists():
            return JsonResponse({'msg': 'Email already registered'}, status=400)

        with transaction.atomic():
            if mode == 'create':
                org_name = data.get('org_name', '').strip()
                if not org_name:
                    return JsonResponse({'msg': 'Organization name is required'}, status=400)

                tenant_id = uuid.uuid4().hex[:12]
                db_password = secrets.token_urlsafe(16)
                key = generate_symmetric_key()

                tenant = Tenant.objects.create(
                    id=tenant_id,
                    organization=org_name,
                    db_user=f"crm_tenant_{tenant_id}",
                    db_user_password=db_password,
                    key=key,
                )

                user = CustomUser.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    phone_number=phone or '',
                    role=CustomUser.ADMIN,
                    organization=org_name,
                    tenant=tenant,
                )

                # Auto-generate a default invite code for the new org
                invite_code = InviteCode.objects.create(
                    code=InviteCode.generate_code(),
                    tenant=tenant,
                    created_by=user,
                    role='employee',
                )

                return JsonResponse({
                    'msg': 'Organization created successfully',
                    'tenant_id': tenant_id,
                    'organization': org_name,
                    'user_id': user.id,
                    'invite_code': invite_code.code,
                })

            else:  # mode == 'join'
                code_str = data.get('invite_code', '').strip().upper()
                if not code_str:
                    return JsonResponse({'msg': 'Invite code is required'}, status=400)

                try:
                    invite = InviteCode.objects.get(code=code_str)
                except InviteCode.DoesNotExist:
                    return JsonResponse({'msg': 'Invalid invite code'}, status=400)

                if not invite.is_valid():
                    return JsonResponse({'msg': 'Invite code is expired or has reached its usage limit'}, status=400)

                tenant = invite.tenant
                role = invite.role or CustomUser.EMPLOYEE

                user = CustomUser.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    phone_number=phone or '',
                    role=role,
                    organization=tenant.organization,
                    tenant=tenant,
                )

                invite.use_count += 1
                invite.save(update_fields=['use_count'])

                return JsonResponse({
                    'msg': 'Joined organization successfully',
                    'tenant_id': tenant.id,
                    'organization': tenant.organization,
                    'user_id': user.id,
                    'role': role,
                })

    except IntegrityError as e:
        logger.error(f"Registration IntegrityError: {e}")
        return JsonResponse({'msg': 'A user with that information already exists'}, status=400)
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return JsonResponse({'msg': str(e)}, status=500)


@csrf_exempt
def validate_invite_code(request):
    if request.method != 'POST':
        return JsonResponse({'msg': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        code_str = data.get('invite_code', '').strip().upper()

        if not code_str or len(code_str) < 6:
            return JsonResponse({'valid': False, 'msg': 'Code too short'}, status=400)

        try:
            invite = InviteCode.objects.select_related('tenant').get(code=code_str)
        except InviteCode.DoesNotExist:
            return JsonResponse({'valid': False, 'msg': 'Invalid invite code'})

        if not invite.is_valid():
            return JsonResponse({'valid': False, 'msg': 'Invite code is expired or used up'})

        return JsonResponse({
            'valid': True,
            'organization': invite.tenant.organization,
            'role': invite.role,
        })

    except Exception as e:
        return JsonResponse({'valid': False, 'msg': str(e)}, status=500)


@csrf_exempt
def register_google(request):
    if request.method != 'POST':
        return JsonResponse({'msg': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip()
        google_uid = data.get('google_uid', '')
        display_name = data.get('display_name', '').strip()
        mode = data.get('mode')  # "create" or "join"
        org_name = data.get('org_name', '').strip()
        invite_code_str = data.get('invite_code', '').strip().upper()

        if not email:
            return JsonResponse({'msg': 'Email is required'}, status=400)

        # Check if user already exists — return their info for auto-login
        existing = CustomUser.objects.filter(email=email).first()
        if existing:
            # Generate a deterministic password for authenticate() call
            username = existing.username
            password = f"{username}nutenai"
            existing.set_password(password)
            existing.save(update_fields=['password'])
            return JsonResponse({
                'status': 'existing_user',
                'username': username,
                'password': password,
                'tenant_id': existing.tenant_id,
                'user_id': existing.id,
                'role': existing.role,
            })

        # New user
        if mode not in ('create', 'join'):
            return JsonResponse({'msg': 'Mode must be "create" or "join"'}, status=400)

        # Derive username from email
        base_username = email.split('@')[0].replace('.', '').replace('+', '')[:20]
        username = base_username
        counter = 1
        while CustomUser.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        password = f"{username}nutenai"

        with transaction.atomic():
            if mode == 'create':
                if not org_name:
                    org_name = display_name or username

                tenant_id = uuid.uuid4().hex[:12]
                db_password = secrets.token_urlsafe(16)
                key = generate_symmetric_key()

                tenant = Tenant.objects.create(
                    id=tenant_id,
                    organization=org_name,
                    db_user=f"crm_tenant_{tenant_id}",
                    db_user_password=db_password,
                    key=key,
                )

                user = CustomUser.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    phone_number='',
                    role=CustomUser.ADMIN,
                    organization=org_name,
                    tenant=tenant,
                )

                invite = InviteCode.objects.create(
                    code=InviteCode.generate_code(),
                    tenant=tenant,
                    created_by=user,
                    role='employee',
                )

                return JsonResponse({
                    'status': 'new_user',
                    'username': username,
                    'password': password,
                    'tenant_id': tenant_id,
                    'organization': org_name,
                    'user_id': user.id,
                    'invite_code': invite.code,
                })

            else:  # join
                if not invite_code_str:
                    return JsonResponse({'msg': 'Invite code is required for join mode'}, status=400)

                try:
                    invite = InviteCode.objects.get(code=invite_code_str)
                except InviteCode.DoesNotExist:
                    return JsonResponse({'msg': 'Invalid invite code'}, status=400)

                if not invite.is_valid():
                    return JsonResponse({'msg': 'Invite code is expired or used up'}, status=400)

                tenant = invite.tenant
                role = invite.role or CustomUser.EMPLOYEE

                user = CustomUser.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    phone_number='',
                    role=role,
                    organization=tenant.organization,
                    tenant=tenant,
                )

                invite.use_count += 1
                invite.save(update_fields=['use_count'])

                return JsonResponse({
                    'status': 'new_user',
                    'username': username,
                    'password': password,
                    'tenant_id': tenant.id,
                    'organization': tenant.organization,
                    'user_id': user.id,
                    'role': role,
                })

    except IntegrityError as e:
        logger.error(f"Google registration IntegrityError: {e}")
        return JsonResponse({'msg': 'A user with that information already exists'}, status=400)
    except Exception as e:
        logger.error(f"Google registration error: {e}")
        return JsonResponse({'msg': str(e)}, status=500)