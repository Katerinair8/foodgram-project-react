from django.contrib.auth import get_user_model
from djoser.serializers import UserCreateSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from api.constants import INTEGER_FIELD_MAX_VALUE, INTEGER_FIELD_MIN_VALUE
from api.utils import recipe_ingredient_create
from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag
from users.models import Subscribe

User = get_user_model()


class UserRegistrationSerializer(UserCreateSerializer):
    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "password",
        )


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
        )

    def get_is_subscribed(self, obj):
        user = self.context["request"].user
        if user.is_anonymous:
            return False
        return Subscribe.objects.filter(user=user, author=obj).exists()


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("id", "name", "color", "slug")


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")


class IngredientRecipeGetSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source="ingredient.id")
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(
        source="ingredient.measurement_unit",
    )

    class Meta:
        model = RecipeIngredient
        fields = ("id", "name", "measurement_unit", "amount")
        validators = [
            UniqueTogetherValidator(
                queryset=RecipeIngredient.objects.all(),
                fields=["ingredient", "recipe"],
            )
        ]


class IngredientRecipeSerializer(serializers.ModelSerializer):
    recipe = serializers.PrimaryKeyRelatedField(read_only=True)
    amount = serializers.IntegerField(
        write_only=True,
        min_value=INTEGER_FIELD_MIN_VALUE,
        max_value=INTEGER_FIELD_MAX_VALUE,
    )
    id = serializers.PrimaryKeyRelatedField(
        source="ingredient", queryset=Ingredient.objects.all()
    )

    class Meta:
        model = RecipeIngredient
        fields = ("id", "amount", "recipe")


class RecipeFollowSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")


class FollowSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source="author.id")
    email = serializers.ReadOnlyField(source="author.email")
    username = serializers.ReadOnlyField(source="author.username")
    first_name = serializers.ReadOnlyField(source="author.first_name")
    last_name = serializers.ReadOnlyField(source="author.last_name")
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.ReadOnlyField(source="author.recipes.count")

    class Meta:
        model = Subscribe
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "recipes",
            "recipes_count",
        )

    def validate(self, data):
        method = self.context["request"].method
        if method == "POST":
            if (Subscribe.objects.filter(
                user=self.context["user"], author=self.context["author"]
            ).exists()):
                raise serializers.ValidationError(
                    "Вы уже подписаны на данного пользователя",
                )
        elif method == "DELETE":
            if not (Subscribe.objects.filter(
                user=self.context["user"], author=self.context["author"]
            ).exists()):
                raise serializers.ValidationError("Ошибка подписки")
        return data

    def get_recipes(self, obj):
        request = self.context["request"]
        limit = request.GET.get("recipes_limit")
        queryset = Recipe.objects.filter(author=obj.author)
        if limit:
            queryset = queryset[: int(limit)]
        return RecipeFollowSerializer(queryset, many=True).data


class RecipeGetSerializer(serializers.ModelSerializer):
    image = Base64ImageField(max_length=None, use_url=True)
    ingredients = serializers.SerializerMethodField()
    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            "id",
            "author",
            "name",
            "text",
            "ingredients",
            "tags",
            "cooking_time",
            "is_favorited",
            "is_in_shopping_cart",
            "image",
        )
        read_only_fields = (
            "id",
            "author",
        )

    def get_is_favorited(self, obj):
        user = self.context["request"].user
        if user.is_anonymous:
            return False
        return obj.favorites.filter(user=user).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context["request"].user
        if user.is_anonymous:
            return False
        return obj.cart.filter(user=user).exists()

    def get_ingredients(self, obj):
        recipe_ingredients = RecipeIngredient.objects.filter(recipe=obj)
        return IngredientRecipeGetSerializer(
            recipe_ingredients,
            many=True,
        ).data


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = IngredientRecipeSerializer(many=True)
    author = UserSerializer(read_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
    )
    image = Base64ImageField(max_length=None, use_url=True)
    cooking_time = serializers.IntegerField(
        min_value=INTEGER_FIELD_MIN_VALUE,
        max_value=INTEGER_FIELD_MAX_VALUE,
    )

    class Meta:
        model = Recipe
        fields = (
            "id",
            "author",
            "name",
            "text",
            "ingredients",
            "tags",
            "cooking_time",
            "image",
        )
        read_only_fields = ("id", "author", "tags")
        extra_kwargs = {
            'ingredients': {'required': True},
            'tags': {'required': True},
        }

    def validate(self, data):
        tags = self.initial_data.get("tags")
        if not len(tags):
            raise serializers.ValidationError(
                "Нужен хотя бы один тег"
            )
        ingredients = self.initial_data.get("ingredients")
        if not len(ingredients):
            raise serializers.ValidationError(
                "Нужен хотя бы один ингредиент"
            )

        ingredients_list = [ingredient["id"] for ingredient in ingredients]
        if len(ingredients_list) != len(set(ingredients_list)):
            raise serializers.ValidationError(
                "Проверьте, какой-то ингредиент был выбран более 1 раза"
            )
        return data

    def create(self, validated_data):
        ingredients_data = validated_data.pop("ingredients")
        tags_data = validated_data.pop("tags")
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_data)
        recipe_ingredient_create(ingredients_data, RecipeIngredient, recipe)
        return recipe

    def update(self, instance, validated_data):
        if "tags" in self.validated_data:
            tags_data = validated_data.pop("tags")
            instance.tags.set(tags_data)
        if "ingredients" in self.validated_data:
            ingredients_data = validated_data.pop("ingredients")
            amount_set = RecipeIngredient.objects.filter(
                recipe__id=instance.id,
            )
            amount_set.delete()
            recipe_ingredient_create(
                ingredients_data,
                RecipeIngredient,
                instance,
            )
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        self.fields.pop("ingredients")
        self.fields.pop("tags")
        representation = super().to_representation(instance)
        representation["ingredients"] = IngredientRecipeGetSerializer(
            RecipeIngredient.objects.filter(recipe=instance), many=True
        ).data
        representation["tags"] = TagSerializer(instance.tags, many=True).data
        return representation
