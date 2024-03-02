from rest_framework import serializers


def required_username(value):
    if value.lower() == 'me':
        raise serializers.ValidationError('Использование имени "me"'
                                          'запрещено.')
