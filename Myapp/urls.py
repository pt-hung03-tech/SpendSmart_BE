from django.urls import path
from . import views

urlpatterns = [
    # Các endpoint API
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('finance-overview/', views.finance_overview, name='finance-overview'),
    path('expense-categories/', views.expense_categories, name='expense-categories'),
    path('transactions/', views.transactions, name='transactions'),
    path('transactions/create/', views.create_transaction, name='create-transaction'),
    path('categories/', views.list_categories, name='list-categories'),  # Lấy danh sách danh mục
    path('categories/create/', views.create_category, name='create-category'),  # Tạo danh mục mới
    path('categories/update/<int:id>/', views.update_category, name='update-category'),  # Cập nhật danh mục
    path('categories/delete/<int:id>/', views.delete_category, name='delete-category'),  # Xóa danh mục
    path('chat/', views.chat_with_ai, name='chat_with_ai'),
]