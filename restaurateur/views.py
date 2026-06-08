from collections import defaultdict

import requests
from django import forms
from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Case, IntegerField, Value, When
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from utils import enrich_restaurants, fetch_coordinates

from foodcartapp.models import Order, Product, Restaurant, RestaurantMenuItem


class Login(forms.Form):
    username = forms.CharField(
        label="Логин",
        max_length=75,
        required=True,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Укажите имя пользователя"}
        ),
    )
    password = forms.CharField(
        label="Пароль",
        max_length=75,
        required=True,
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Введите пароль"}
        ),
    )


class LoginView(View):
    def get(self, request, *args, **kwargs):
        form = Login()
        return render(request, "login.html", context={"form": form})

    def post(self, request):
        form = Login(request.POST)

        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.is_staff:  # FIXME replace with specific permission
                    return redirect("restaurateur:RestaurantView")
                return redirect("start_page")

        return render(
            request,
            "login.html",
            context={
                "form": form,
                "ivalid": True,
            },
        )


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy("restaurateur:login")


def is_manager(user):
    return user.is_staff  # FIXME replace with specific permission


@user_passes_test(is_manager, login_url="restaurateur:login")
def view_products(request):
    restaurants = list(Restaurant.objects.order_by("name"))
    products = list(Product.objects.prefetch_related("menu_items"))

    products_with_restaurant_availability = []
    for product in products:
        availability = {
            item.restaurant_id: item.availability for item in product.menu_items.all()
        }
        ordered_availability = [
            availability.get(restaurant.id, False) for restaurant in restaurants
        ]

        products_with_restaurant_availability.append((product, ordered_availability))

    return render(
        request,
        template_name="products_list.html",
        context={
            "products_with_restaurant_availability": products_with_restaurant_availability,
            "restaurants": restaurants,
        },
    )


@user_passes_test(is_manager, login_url="restaurateur:login")
def view_restaurants(request):
    return render(
        request,
        template_name="restaurants_list.html",
        context={
            "restaurants": Restaurant.objects.all(),
        },
    )


@user_passes_test(is_manager, login_url="restaurateur:login")
def view_orders(request):
    orders = (
        Order.objects.with_price()
        .with_items_prefetched()
        .order_by(
            Case(
                When(order_status=Order.OrderStatus.NEW, then=Value(1)),
                When(order_status=Order.OrderStatus.COOKING, then=Value(2)),
                default=Value(3),
                output_field=IntegerField(),
            )
        )
    )

    all_product_ids = set()
    for order in orders:
        for item in order.items.all():
            all_product_ids.add(item.product_id)

    product_restaurants = defaultdict(set)
    if all_product_ids:
        menu_items = RestaurantMenuItem.objects.filter(
            product_id__in=all_product_ids, availability=True
        ).values_list("product_id", "restaurant_id")
        for product_id, restaurant_id in menu_items:
            product_restaurants[product_id].add(restaurant_id)

    restaurant_cache = {rest.id: rest for rest in Restaurant.objects.all()}

    orders_with_availability = []
    for order in orders:
        try:
            order_lon, order_lat = fetch_coordinates(address=order.address)
            order_coords = (float(order_lat), float(order_lon))
        except requests.exceptions.RequestException:
            order_coords = None

        product_ids = [item.product_id for item in order.items.all()]

        if not product_ids:
            available_restaurants = []
        else:
            available_restaurant_ids = set(
                product_restaurants.get(product_ids[0], set())
            )
            for product_id in product_ids[1:]:
                available_restaurant_ids &= product_restaurants.get(product_id, set())
                if not available_restaurant_ids:
                    break

            available_restaurants = [
                restaurant_cache[rest_id]
                for rest_id in available_restaurant_ids
                if rest_id in restaurant_cache
            ]

        if order_coords is not None:
            available_restaurant_with_distance = enrich_restaurants(
                order_coords,
                available_restaurants,
            )
        else:
            available_restaurant_with_distance = [
                {"restaurant": rest, "distance": None} for rest in available_restaurants
            ]

        orders_with_availability.append(
            {
                "order": order,
                "available_restaurants": available_restaurant_with_distance,
            }
        )

    return render(
        request, "order_items.html", context={"order_items": orders_with_availability}
    )
