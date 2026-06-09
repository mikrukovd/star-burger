import requests
from django.conf import settings
from geopy.distance import distance

from places.models import Place


def fetch_coordinates(address):
    """Возвращает координаты по адресу"""
    base_url = "https://geocode-maps.yandex.ru/1.x"
    response = requests.get(
        base_url,
        params={
            "geocode": address,
            "apikey": settings.YANDEX_GEOCODER_APIKEY,
            "format": "json",
        },
    )
    response.raise_for_status()
    found_places = response.json()["response"]["GeoObjectCollection"]["featureMember"]

    if not found_places:
        return None

    most_relevant = found_places[0]
    lon, lat = most_relevant["GeoObject"]["Point"]["pos"].split(" ")

    Place.objects.update_or_create(
        address=address,
        defaults={"lon": lon, "lat": lat},
    )

    return lon, lat


def enrich_restaurants(order_coords, available_restaurants, places_cache):
    """Вернет список ресторанов с координатами"""
    result = []

    for restaurant in available_restaurants:
        try:
            place = places_cache.get(restaurant.address)

            if place:
                lon, lat = place.lon, place.lat
            else:
                coords = fetch_coordinates(restaurant.address)

                if not coords:
                    continue

                lon, lat = coords
                places_cache[restaurant.address] = Place(
                    address=restaurant.address, lon=lon, lat=lat
                )

            restaurant_coords = (float(lat), float(lon))
            dist = distance(order_coords, restaurant_coords).km

            result.append({"restaurant": restaurant, "distance": dist})

        except requests.exceptions.RequestException:
            continue

    return sorted(result, key=lambda x: x["distance"])
