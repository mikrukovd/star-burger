from collections import defaultdict

import requests

from foodcartapp.models import Restaurant, RestaurantMenuItem
from places.models import Place
from places.utils import fetch_coordinates


def get_product_restaurants(orders):
    """Вернет dict {product_id: set(restaurant_id)} для всех товаров в заказах"""
    all_product_ids = {
        item.product_id for order in orders for item in order.items.all()
    }

    product_restaurants = defaultdict(set)

    if all_product_ids:
        menu_items = RestaurantMenuItem.objects.filter(
            product_id__in=all_product_ids,
            availability=True,
        ).values_list("product_id", "restaurant_id")

        for product_id, restaurant_id in menu_items:
            product_restaurants[product_id].add(restaurant_id)

    return product_restaurants


def get_available_restaurants_for_order(order, product_restaurants, restaurants_by_id):
    """Вернет список доступных Restaurant для выполнения заказа"""
    product_ids = [item.product_id for item in order.items.all()]

    if not product_ids:
        return []

    available_ids = set(product_restaurants.get(product_ids[0], set()))
    for product_id in product_ids[1:]:
        available_ids &= product_restaurants.get(product_id, set())
        if not available_ids:
            break

    return [
        restaurants_by_id[restaurant_id]
        for restaurant_id in available_ids
        if restaurant_id in restaurants_by_id
    ]


def get_order_coords(order, places_cache):
    """
    Вернет кортеж с координатами и флагом address_not_found
    Обновит координаты при обращении к API
    """
    place = places_cache.get(order.address)

    if place:
        return (float(place.lat), float(place.lon)), False

    try:
        coords = fetch_coordinates(order.address)
        if coords:
            lon, lat = coords
            places_cache[order.address] = Place(address=order.address, lon=lon, lat=lat)
            return (float(lat), float(lon)), False
        return None, True
    except requests.exceptions.RequestException:
        return None, True


def build_places_cache(orders, restaurants_by_id):
    """Загружает Place в одном запросе"""
    order_addresses = {order.address for order in orders}
    restaurant_addresses = {
        restaurant.address for restaurant in restaurants_by_id.values()
    }

    return {
        place.address: place
        for place in Place.objects.filter(
            address__in=order_addresses | restaurant_addresses
        )
    }


def build_restaurants_by_id(orders, product_restaurants):
    """Загружает рестораны для всех заказов в одном запросе"""
    all_available_restaurant_ids = set()

    for order in orders:
        product_ids = [item.product_id for item in order.items.all()]
        if product_ids:
            ids = set(product_restaurants.get(product_ids[0], set()))
            for product_id in product_ids[1:]:
                ids &= product_restaurants.get(product_id, set())
                if not ids:
                    break
            all_available_restaurant_ids |= ids

    return {
        restaurant.id: restaurant
        for restaurant in Restaurant.objects.filter(id__in=all_available_restaurant_ids)
    }
