from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import DecimalField, F, Prefetch, Sum
from phonenumber_field.modelfields import PhoneNumberField


class OrderQuerySet(models.QuerySet):
    def with_price(self):
        return self.annotate(
            price=Sum(
                F("items__quantity") * F("items__price"),
                output_field=DecimalField(max_digits=10, decimal_places=2),
            )
        )

    def with_items_prefetched(self):
        return self.prefetch_related(
            Prefetch("items", queryset=OrderItem.objects.select_related("product"))
        )


class Restaurant(models.Model):
    name = models.CharField("название", max_length=50)
    address = models.CharField(
        "адрес",
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        "контактный телефон",
        max_length=50,
        blank=True,
    )

    class Meta:
        verbose_name = "ресторан"
        verbose_name_plural = "рестораны"

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = RestaurantMenuItem.objects.filter(availability=True).values_list(
            "product"
        )
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField("название", max_length=50)

    class Meta:
        verbose_name = "категория"
        verbose_name_plural = "категории"

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField("название", max_length=50)
    category = models.ForeignKey(
        ProductCategory,
        verbose_name="категория",
        related_name="products",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        "цена", max_digits=8, decimal_places=2, validators=[MinValueValidator(0)]
    )
    image = models.ImageField("картинка")
    special_status = models.BooleanField(
        "спец.предложение",
        default=False,
        db_index=True,
    )
    description = models.TextField(
        "описание",
        max_length=200,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = "товар"
        verbose_name_plural = "товары"

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name="menu_items",
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="menu_items",
        verbose_name="продукт",
    )
    availability = models.BooleanField("в продаже", default=True, db_index=True)

    class Meta:
        verbose_name = "пункт меню ресторана"
        verbose_name_plural = "пункты меню ресторана"
        unique_together = [["restaurant", "product"]]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"


class Order(models.Model):
    class OrderStatus(models.TextChoices):
        NEW = "new", "Необработанный"
        COOKING = "cooking", "Готовится"
        CANCELED = "canceled", "Отменён"
        PREPARING = "preparing", "В сборке"
        DELIVERING = "delivering", "В доставке"
        DELIVERED = "delivered", "Доставлен"

    class PaymentStatus(models.TextChoices):
        CARD = "card", "Карта"
        MONEY = "money", "Наличные"

    order_status = models.CharField(
        "статус заказа",
        max_length=50,
        choices=OrderStatus.choices,
        default=OrderStatus.NEW,
    )
    payment_status = models.CharField(
        "способ оплаты",
        max_length=50,
        choices=PaymentStatus,
    )
    firstname = models.CharField("имя", max_length=50)
    lastname = models.CharField("фамилия", max_length=50)

    phonenumber = PhoneNumberField(
        "телефон",
        region="RU",
        db_index=True,
    )

    address = models.CharField(
        "адрес доставки",
        max_length=255,
    )
    restaurant = models.ForeignKey(
        Restaurant,
        related_name="orders",
        verbose_name="ресторан",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    comment = models.TextField("комментарий к заказу", blank=True)
    created_at = models.DateTimeField(
        "создан",
        auto_now_add=True,
    )
    called_at = models.DateTimeField("дата звонка", blank=True, null=True)
    delivered_at = models.DateTimeField("доставлен", blank=True, null=True)

    objects = OrderQuerySet.as_manager()

    class Meta:
        verbose_name = "заказ"
        verbose_name_plural = "заказы"
        indexes = [
            models.Index(fields=["created_at"]),
            models.Index(fields=["order_status"]),
            models.Index(fields=["payment_status"]),
            models.Index(fields=["called_at"]),
            models.Index(fields=["delivered_at"]),
        ]

    def __str__(self):
        return f"Заказ #{self.id}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        related_name="items",
        on_delete=models.CASCADE,
        verbose_name="заказ",
    )

    product = models.ForeignKey(
        Product,
        related_name="order_items",
        on_delete=models.CASCADE,
        verbose_name="товар",
    )

    quantity = models.PositiveIntegerField(
        "количество",
        validators=[MinValueValidator(1)],
    )

    price = models.DecimalField(
        "цена",
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )

    class Meta:
        verbose_name = "позиция заказа"
        verbose_name_plural = "позиции заказа"

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
