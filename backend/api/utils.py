from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.response import Response

from .exceptions import BadRequestException


def get_object_or_400(error_text, model, **data):
    try:
        obj = model.objects.get(**data)
        return obj
    except model.DoesNotExist:
        raise BadRequestException(detail=error_text, code=400)


def add_delete_to(request, pk, model, obj_field_name, obj_not_exist_text,
                  relation_exist_text, relation_not_exist_text,
                  relation_model, serializer_class, is_recipe_model):
    user = request.user
    if request.method == 'POST':
        if is_recipe_model:
            obj = get_object_or_400(obj_not_exist_text, model, id=pk)
        else:
            obj = get_object_or_404(model, id=pk)
        if obj == user:
            context = {
                'errors': 'Нельзя подписаться на себя!'
            }
            return Response(context, status=status.HTTP_400_BAD_REQUEST)
        data = {
            'user': user,
            obj_field_name: obj
        }
        relation, created = relation_model.objects.get_or_create(**data)
        if created:
            if is_recipe_model:
                serializer = serializer_class(
                    obj,
                    context={'request': request},
                    fields=('id', 'name', 'image', 'cooking_time')
                )
            else:
                serializer = serializer_class(
                    obj,
                    context={'request': request},
                )
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        context = {
            'errors': relation_exist_text
        }
        return Response(context, status=status.HTTP_400_BAD_REQUEST)
    if request.method == 'DELETE':
        obj = get_object_or_404(model, id=pk)
        data = {
            'user': user,
            obj_field_name: obj
        }
        relation = get_object_or_400(
            relation_not_exist_text,
            relation_model,
            **data
        )
        relation.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


def list_related_recipes(self, queryset, value,
                         relation_model, related_name):
    user = self.request.user.id
    if bool(value):
        return queryset.filter(
            id__in=relation_model.objects.filter(
                user=user).values('recipe_id')).order_by(
                    '__'.join([related_name, 'created_at'])
        )
    return queryset
