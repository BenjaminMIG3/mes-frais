import re
from rest_framework import serializers
from django.contrib.auth import authenticate

class AuthSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            raise serializers.ValidationError("Informations manquantes.")
        
        user = authenticate(username=username, password=password)
        if user is None:
            raise serializers.ValidationError("Identifiants invalides.")
        
        data['user'] = user
        return data