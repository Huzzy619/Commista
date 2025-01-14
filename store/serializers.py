from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from store.models import Cart, CartItem, Colour, ColourInventory, Product, ProductReview, Size, SizeInventory


class ColourSerializer(serializers.ModelSerializer):
    class Meta:
        model = Colour
        fields = ['name', 'hex_code']


class ColourInventorySerializer(serializers.ModelSerializer):
    colour = ColourSerializer()

    class Meta:
        model = ColourInventory
        fields = ['colour', 'quantity', 'extra_price']


class SizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Size
        fields = ['title']


class SizeInventorySerializer(serializers.ModelSerializer):
    size = SizeSerializer()

    class Meta:
        model = SizeInventory
        fields = ['size', 'quantity', 'extra_price']


class ProductSerializer(serializers.ModelSerializer):
    sizes = SizeInventorySerializer(source='size_inventory', many=True, read_only=True)
    colours = ColourInventorySerializer(source='colour_inventory', many=True, read_only=True)
    images = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'title', 'slug', 'category', 'description', 'style', 'price', 'percentage_off', 'images',
                  'colours', 'sizes']

    @staticmethod
    def get_images(obj):
        return [image.image_url() for image in obj.images.all()]


class ProductDetailSerializer(ProductSerializer):
    inventory = serializers.IntegerField()
    condition = serializers.CharField()
    location = serializers.CharField()
    discount_price = serializers.DecimalField(max_digits=6, decimal_places=2)
    average_ratings = serializers.DecimalField(max_digits=3, decimal_places=2)

    class Meta:
        model = Product
        fields = ProductSerializer.Meta.fields + ['inventory', 'condition', 'location', 'discount_price',
                                                  'average_ratings']


class ProductReviewSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name')

    class Meta:
        model = ProductReview
        fields = ('customer_name', 'ratings', 'description')


class AddProductReviewSerializer(serializers.ModelSerializer):
    images = serializers.ListField(child=serializers.ImageField(), required=False, max_length=3)

    class Meta:
        model = ProductReview
        fields = ['id', 'ratings', 'description', 'images']

    @staticmethod
    def validate_id(value):
        if not Product.categorized.filter(id=value).exists():
            raise ValidationError("This product does not exist, try again")
        return value


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer()
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['cart_id', 'product', 'quantity', 'total_price']

    @staticmethod
    def get_total_price(cartitem: CartItem):
        if cartitem.product.discount_price > 0:
            return cartitem.quantity * cartitem.product.discount_price
        return cartitem.quantity * cartitem.product.price


class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = ['id', 'items', 'total_price']


def validate_cart_item(self, attrs):
    product_id = attrs['product_id']
    if not Product.objects.filter(id=product_id).exists():
        raise serializers.ValidationError({"message": "No product with the given ID was found."})

    product = Product.objects.get(id=product_id)
    size = attrs.get('size', '')
    if size and not product.size.filter(title=size).exists():
        raise serializers.ValidationError({"message": "Size not found for the given product.", "status": "failed"})

    colour = attrs.get('colour', '')
    if colour and not product.colour.filter(name=colour).exists():
        raise serializers.ValidationError({"message": "Colour not found for the given product.", "status": "failed"})

    return attrs


class AddCartItemSerializer(serializers.Serializer):
    cart_id = serializers.CharField(max_length=60, required=False, default=None)
    product_id = serializers.CharField(max_length=100)
    size = serializers.CharField(required=False)
    colour = serializers.CharField(required=False)
    quantity = serializers.IntegerField()

    def validate(self, attrs):
        attrs = validate_cart_item(attrs)
        return attrs

    def save(self, **kwargs):
        product = Product.objects.get(id=self.validated_data['product_id'])
        cart_id = self.validated_data.get('cart_id')
        size = self.validated_data.get('size', None)
        colour = self.validated_data.get('colour', None)
        quantity = self.validated_data.get('quantity')

        if cart_id is None:
            cart = Cart.objects.create()
            # cart_id = cart.id
        else:
            cart, _ = Cart.objects.get_or_create(id=cart_id)

        try:
            item = CartItem.objects.get(cart=cart, product=product, size=size, colour=colour)
            item.quantity += quantity
            item.save()
        except CartItem.DoesNotExist:
            item = CartItem.objects.create(cart=cart, product=product, size=size, colour=colour, quantity=quantity)
        if item.quantity == 0:
            item.delete()

        if cart.items.count() == 0:
            cart.delete()
        return item


class UpdateCartItemSerializer(serializers.Serializer):
    cart_id = serializers.CharField(max_length=60, default=None)
    product_id = serializers.CharField(max_length=100)
    size = serializers.CharField(required=False)
    colour = serializers.CharField(required=False)

    def validate(self, attrs):
        attrs = validate_cart_item(attrs)
        return attrs

    def save(self, **kwargs):
        try:
            cart = Cart.objects.get(id=self.validated_data['cart_id'])
            product = Product.objects.get(id=self.validated_data['product_id'])
            item = CartItem.objects.get(cart=cart, product=product)
        except (Cart.DoesNotExist, Product.DoesNotExist, CartItem.DoesNotExist):
            raise serializers.ValidationError(
                    {"message": "Invalid cart or product ID. Please check the provided IDs.", "status": "failed"})
        if self.validated_data.get('size'):
            item.size = self.validated_data['size']
        if self.validated_data.get('colour'):
            item.colour = self.validated_data['colour']
        item.save()
        return item


class DeleteCartItemSerializer(serializers.Serializer):
    cart_id = serializers.CharField(max_length=60, required=True)
    product_id = serializers.CharField(max_length=100, required=True)

    def save(self, **kwargs):
        try:
            cart = Cart.objects.get(id=self.validated_data['cart_id'])
            product = Product.objects.get(id=self.validated_data['product_id'])
            item = CartItem.objects.get(cart=cart, product=product)
        except (Cart.DoesNotExist, Product.DoesNotExist, CartItem.DoesNotExist):
            raise serializers.ValidationError(
                    {"message": "Invalid cart or product ID. Please check the provided IDs.", "status": "failed"})
        item.delete()
