from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Category

@receiver(post_save, sender=User)
def create_default_categories(sender, instance, created, **kwargs):
    if created:  # Chỉ chạy khi user mới được tạo
        default_categories = [
            {'name': 'Ăn uống', 'color': '#2ecc71', 'type': 'expense', 'owner': instance},
            {'name': 'Đi lại', 'color': '#3498db', 'type': 'expense', 'owner': instance},
            {'name': 'Sinh hoạt', 'color': '#e74c3c', 'type': 'expense', 'owner': instance},
            {'name': 'Lương', 'color': '#f1c40f', 'type': 'income', 'owner': instance},
            {'name': 'Khác', 'color': '#9b59b6', 'type': 'income', 'owner': instance},
        ]
        for category_data in default_categories:
            Category.objects.get_or_create(**category_data)
            print(f"Created default category '{category_data['name']}' for new user '{instance.username}'")