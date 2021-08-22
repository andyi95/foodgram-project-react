from rest_framework import serializers
from users.models import User

from api.models import Follow


class UserSerializerCom(serializers.ModelSerializer):
    """
    Модель пользователя, используемая в настройках Djoser для отображения
    """
    is_subscribed = serializers.SerializerMethodField('get_is_subscribed')

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username',
            'first_name', 'last_name', 'is_subscribed'
        )

    def get_is_subscribed(self, author):
        request = self.context.get('request')
        return Follow.objects.filter(
            user=request.user, author=author
        ).exists()


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name')
