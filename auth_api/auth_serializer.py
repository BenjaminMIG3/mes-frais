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
        
        # Regex sur le mail
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', username):
            raise serializers.ValidationError("Adresse mail invalide.")

        user = authenticate(username=username, password=password)
        if user is None:
            raise serializers.ValidationError("Identifiants invalides.")
        data['user'] = user
        return data