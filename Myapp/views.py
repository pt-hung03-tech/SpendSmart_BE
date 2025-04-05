from django.shortcuts import render
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.contrib.auth import authenticate, login as auth_login
from django.views.decorators.csrf import csrf_exempt
from http import HTTPStatus
import json
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Sum
from .models import Transaction, Category
from .serializers import TransactionSerializer, CategorySerializer
from decouple import config
import google.generativeai as genai


@csrf_exempt
def register(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            username = data.get("username")
            password = data.get("password")

            # Kiểm tra username và password có được cung cấp không
            if not username or not password:
                return JsonResponse({"error": "❌ Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu!"}, status=HTTPStatus.BAD_REQUEST)

            # Kiểm tra username đã tồn tại chưa
            if User.objects.filter(username=username).exists():
                return JsonResponse({"error": "❌ Tên đăng nhập đã tồn tại!"}, status=HTTPStatus.BAD_REQUEST)

            # Tạo người dùng mới
            user = User.objects.create_user(username=username, password=password)
            return JsonResponse({"message": "✅ Đăng ký thành công!"}, status=HTTPStatus.CREATED)
        except json.JSONDecodeError:
            return JsonResponse({"error": "❌ Dữ liệu JSON không hợp lệ!"}, status=HTTPStatus.BAD_REQUEST)
    
    # Trả về lỗi nếu phương thức không phải POST
    return JsonResponse({"error": "❌ Phương thức không được hỗ trợ!"}, status=HTTPStatus.METHOD_NOT_ALLOWED)

@csrf_exempt
def login(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')

            if not username or not password:
                return JsonResponse({"error": "❌ Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu!"}, status=HTTPStatus.BAD_REQUEST)

            user = authenticate(username=username, password=password)
            if user is not None:
                token, created = Token.objects.get_or_create(user=user)
                return JsonResponse({"message": "✅ Đăng nhập thành công!", "token": token.key}, status=HTTPStatus.OK)
            else:
                return JsonResponse({"error": "❌ Tên đăng nhập hoặc mật khẩu không chính xác!"}, status=HTTPStatus.BAD_REQUEST)
        except json.JSONDecodeError:
            return JsonResponse({"error": "❌ Dữ liệu JSON không hợp lệ!"}, status=HTTPStatus.BAD_REQUEST)
    
    return JsonResponse({"error": "❌ Phương thức không được hỗ trợ!"}, status=HTTPStatus.METHOD_NOT_ALLOWED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def finance_overview(request):
    # Tính toán các thống kê
    income = Transaction.objects.filter(
        owner=request.user,
        type='income'
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    expense = Transaction.objects.filter(
        owner=request.user,
        type='expense'
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    return Response({
        'balance': income - expense,
        'income': income,
        'expense': expense
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def expense_categories(request):
    categories = Category.objects.filter(owner=request.user)
    data = []
    
    for category in categories:
        total = Transaction.objects.filter(
            owner=request.user,
            category=category,
            type='expense'
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        data.append({
            'name': category.name,
            'amount': total,
            'color': category.color
        })
    
    return Response(data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def transactions(request):
    transactions = Transaction.objects.filter(owner=request.user).order_by('-date')
    serializer = TransactionSerializer(transactions, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_transaction(request):
    data = request.data.copy()
    
    print('Received Data:', data)
    
    # Kiểm tra category nếu có
    category_id = data.get('category')
    if category_id:
        try:
            Category.objects.get(id=category_id, owner=request.user)
        except Category.DoesNotExist:
            print(f'Category {category_id} does not exist for user {request.user.id}')
            category, _ = Category.objects.get_or_create(
                owner=request.user,
                name='Khác',
                defaults={'color': '#9b59b6', 'type': 'expense'}
            )
            data['category'] = category.id
    
    serializer = TransactionSerializer(data=data, context={'request': request})
    if serializer.is_valid():
        serializer.save(owner=request.user)  # Truyền owner trực tiếp
        print('Saved Transaction:', serializer.data)
        return Response(serializer.data, status=201)
    print('Serializer Errors:', serializer.errors)
    return Response(serializer.errors, status=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_categories(request):
    category_type = request.query_params.get('type', 'expense')
    categories = Category.objects.filter(owner=request.user, type=category_type)
    serializer = CategorySerializer(categories, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_category(request):
    serializer = CategorySerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(owner=request.user)
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_category(request, id):
    try:
        category = Category.objects.get(id=id, owner=request.user)
    except Category.DoesNotExist:
        return Response({"error": "Danh mục không tồn tại"}, status=404)
    serializer = CategorySerializer(category, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=400)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_category(request, id):
    try:
        category = Category.objects.get(id=id, owner=request.user)
    except Category.DoesNotExist:
        return Response({"error": "Danh mục không tồn tại"}, status=404)
    category.delete()
    return Response({"message": "Danh mục đã được xóa"}, status=204)

#AI Chat Bot
genai.configure(api_key=config('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-1.5-flash')
@csrf_exempt
@permission_classes([IsAuthenticated])
def chat_with_ai(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '')

            if not user_message:
                return JsonResponse({'error': 'Vui lòng gửi tin nhắn'}, status=400)

            # Định dạng prompt với context tài chính
            formatted_prompt = f"Với vai trò là người muốn hỏi về vấn đề tài chính, tôi muốn hỏi là: {user_message}"

            # Gửi tin nhắn đã định dạng đến Gemini API
            response = model.generate_content(formatted_prompt)
            ai_text = response.text

            # Trả về phản hồi
            return JsonResponse({
                'text': ai_text,
                'time0': response.created_at.strftime('%H:%M') if hasattr(response, 'created_at') else 'N/A',
                'isAI': True
            })
        except Exception as e:
            return JsonResponse({'error': f'Có lỗi xảy ra: {str(e)}'}, status=500)
    return JsonResponse({'error': 'Phương thức không được hỗ trợ'}, status=405)