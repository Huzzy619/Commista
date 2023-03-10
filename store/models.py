from accounts.validators import validate_phone_number
from autoslug import AutoSlugField
from common.models import BaseModel
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

from store.choices import PAYMENT_STATUS, PAYMENT_PENDING

# Create your models here.

Customer = get_user_model()


class Category(BaseModel):
    title = models.CharField(max_length=255)


class Size(BaseModel):
    title = models.CharField(max_length=5)


class Colour(BaseModel):
    name = models.CharField(max_length=20)
    hex_code = models.CharField(max_length=20)


class Product(BaseModel):
    title = models.CharField(max_length=255)
    slug = AutoSlugField(
        populate_from="title", unique=True, always_update=True, editable=False
    )
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="products"
    )
    description = models.TextField()
    style = models.CharField()
    price = models.DecimalField(max_digits=6, decimal_places=2)
    percentage_off = models.PositiveIntegerField(default=0)
    size = models.ManyToManyField(Size)
    colour = models.ManyToManyField(Colour)
    ratings = models.IntegerField(default=0)
    inventory = models.PositiveIntegerField()

    @property
    def discount_price(self):
        if self.percentage_off > 0:
            discount = self.price - (self.price * self.percentage_off)
        return discount


class Order(BaseModel):
    placed_at = models.DateTimeField(auto_now_add=True)
    payment_status = models.CharField(choices=PAYMENT_STATUS, default=PAYMENT_PENDING)


class Country(BaseModel):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=10)


class Address(BaseModel):
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="addresses"
    )
    country = models.ForeignKey(Country, on_delete=models.PROTECT)
    first_name = models.CharField(_("First name"), max_length=255)
    last_name = models.CharField(_("Last name"), max_length=255)  #
    street_address = models.CharField(max_length=255)
    second_street_address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    zip_code = models.CharField(max_length=10)
    phone_number = models.CharField(max_length=20, validators=[validate_phone_number])
