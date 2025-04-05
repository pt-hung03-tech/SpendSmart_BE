from rest_framework import serializers
from .models import Transaction, Category
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']

class CategorySerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    class Meta:
        model = Category
        fields = ['id', 'name', 'color', 'type']
        extra_kwargs = {
            'owner': {'read_only': True, 'write_only': True}
        }

class TransactionSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Transaction
        fields = ['id', 'date', 'description', 'amount', 'type', 'category', 'category_id', 'owner']
        read_only_fields = ['owner']

    def validate_category_id(self, value):
        if value and not Category.objects.filter(id=value.id, owner=self.context['request'].user).exists():
            raise serializers.ValidationError("Danh mục không tồn tại hoặc không thuộc về bạn")
        return value