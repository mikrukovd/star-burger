import requests
from django.conf import settings
from geopy.distance import distance

from places.models import Place


def fetch_coordinates(address):
    try:
        place = Place.objects.get(address=address)
        return place.lon, place.lat
    except Place.DoesNotExist:
        pass

    # если нет в бд
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

    Place.objects.update_or_create(address=address, defaults={"lon": lon, "lat": lat})

    return lon, lat


def enrich_restaurants(order_coords, available_restaurants):
    result = []

    for restaurant in available_restaurants:
        try:
            lon, lat = fetch_coordinates(address=restaurant.address)
            restaurant_coords = (float(lat), float(lon))
            dist = distance(order_coords, restaurant_coords).km
        except requests.exceptions.RequestException:
            pass  # пропуск ресторана без дистанции если гео не доступен

        result.append(
            {
                "restaurant": restaurant,
                "distance": dist,
            }
        )

    return sorted(result, key=lambda x: x["distance"])
