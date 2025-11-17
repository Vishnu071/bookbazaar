from rest_framework import serializers
from .models import Book, Category

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']

class BookSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)
    cover = serializers.ImageField(read_only=True)

    class Meta:
        model = Book
        fields = ['id', 'title', 'slug', 'description', 'author', 'price', 'stock', 'categories', 'cover']
