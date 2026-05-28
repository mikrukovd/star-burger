from django.http import JsonResponse
from django.templatetags.static import static

from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer

from .models import Order, OrderItem, Product


class OrderItemSerializer(ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["product", "quantity"]


class OrderSerializer(ModelSerializer):
    products = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = ["firstname", "lastname", "phonenumber", "address", "products"]

    def validate_products(self, value):
        if not value:
            raise serializers.ValidationError("Этот список не может быть пустым.")
        return value


def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse(
        [
            {
                "title": "Burger",
                "src": static("burger.jpg"),
                "text": "Tasty Burger at your door step",
            },
            {
                "title": "Spices",
                "src": static("food.jpg"),
                "text": "All Cuisines",
            },
            {
                "title": "New York",
                "src": static("tasty.jpg"),
                "text": "Food is incomplete without a tasty dessert",
            },
        ],
        safe=False,
        json_dumps_params={
            "ensure_ascii": False,
            "indent": 4,
        },
    )


def product_list_api(request):
    products = Product.objects.select_related("category").available()

    dumped_products = []
    for product in products:
        dumped_product = {
            "id": product.id,
            "name": product.name,
            "price": product.price,
            "special_status": product.special_status,
            "description": product.description,
            "category": {
                "id": product.category.id,
                "name": product.category.name,
            }
            if product.category
            else None,
            "image": product.image.url,
            "restaurant": {
                "id": product.id,
                "name": product.name,
            },
        }
        dumped_products.append(dumped_product)
    return JsonResponse(
        dumped_products,
        safe=False,
        json_dumps_params={
            "ensure_ascii": False,
            "indent": 4,
        },
    )


@api_view(["POST"])
def register_order(request):

    serializer = OrderSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    # order_details = request.data

    # if "products" not in order_details:
    #     return Response(
    #         {"error": "products: Обязательное поле."},
    #         status=400,
    #     )

    # if order_details["products"] is None:
    #     return Response(
    #         {"error": "products: Это поле не может быть пустым."},
    #         status=400,
    #     )

    # if isinstance(order_details["products"], str):
    #     return Response(
    #         {"error": "products: Ожидался list со значениями, но был получен 'str'"},
    #         status=400,
    #     )

    # if order_details["products"] == []:
    #     return Response(
    #         {"error": "products: Этот список не может быть пустым."},
    #         status=400,
    #     )

    # if order_details["firstname"] is None:
    #     return Response(
    #         {"error": "firstname: Это поле не может быть пустым."},
    #         status=400,
    #     )

    # if ("firstname", "lastname", "phonenumber", "address") not in order_details:
    #     return Response(
    #         {"error": "firstname, lastname, phonenumber, address: Обязательное поле."},
    #         status=400,
    #     )

    # if ("firstname", "lastname", "phonenumber", "address") in order_details and (
    #     order_details["firstname"] is None
    #     or order_details["lastname"] is None
    #     or order_details["phonenumber"] is None
    #     or order_details["address"] is None
    # ):
    #     return Response(
    #         {
    #             "error": "firstname, lastname, phonenumber, address: Это поле не может быть пустым."
    #         },
    #         status=400,
    #     )
    # if order_details["phonenumber"] == "":
    #     return Response(
    #         {"error": "phonenumber: Это поле не может быть пустым."},
    #         status=400,
    #     )

    # if order_details["phonenumber"] == "+70000000000":
    #     return Response(
    #         {"error": "phonenumber': Введен некорректный номер телефона."},
    #         status=400,
    #     )
    # if any(item["product"] == 9999 for item in order_details["products"]):
    #     return Response(
    #         {"error": "products: Недопустимый первичный ключ '9999'"},
    #         status=400,
    #     )
    # if order_details["firstname"] == []:
    #     return Response({"error": "firstname: Not a valid string."}, status=400)

    order = Order.objects.create(
        firstname=serializer.validated_data["firstname"],
        lastname=serializer.validated_data["lastname"],
        phonenumber=serializer.validated_data["phonenumber"],
        address=serializer.validated_data["address"],
    )
    for item in serializer.validated_data["products"]:
        OrderItem.objects.create(
            order=order, product=item["product"], quantity=item["quantity"]
        )
    # order = Order.objects.create(
    #     first_name=order_details["firstname"],
    #     last_name=order_details["lastname"],
    #     phone_number=order_details["phonenumber"],
    #     address=order_details["address"],
    # )
    # for item in order_details["products"]:
    #     product = Product.objects.get(id=item["product"])

    #     OrderItem.objects.create(
    #         order=order,
    #         product=product,
    #         quantity=item["quantity"],
    #     )

    # TODO это лишь заглушка
    return Response({})
