from django.db.models import Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.filters import SearchFilter
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from store.choices import GENDER_FEMALE, GENDER_MALE
from store.filters import ProductFilter
from store.models import Cart, Category, FavoriteProduct, Notification, Product, ProductReview, ProductReviewImage
from store.serializers import AddCartItemSerializer, AddProductReviewSerializer, CartItemSerializer, \
    DeleteCartItemSerializer, ProductDetailSerializer, \
    ProductReviewSerializer, \
    ProductSerializer, UpdateCartItemSerializer


# Create your views here.

class CategoryAndSalesView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProductSerializer

    def get(self, request):
        categories = Category.objects.values('id', 'title')
        products_without_flash_sales = Product.categorized.filter(flash_sale_start_date=None, flash_sale_end_date=None)
        flash_sales = Product.categorized.filter(flash_sale_start_date__lte=timezone.now(),
                                                 flash_sale_end_date__gte=timezone.now())
        serializer = self.serializer_class(many=True)
        mega_sales = products_without_flash_sales.filter(percentage_off__gte=24)
        products_without_flash_sales_data = serializer.to_representation(products_without_flash_sales)
        flash_sales_data = serializer.to_representation(flash_sales)
        mega_sales_data = serializer.to_representation(mega_sales)

        data = {'categories': categories, 'product_without_flash_sales': products_without_flash_sales_data,
                'flash_sales': flash_sales_data, 'mega_sales': mega_sales_data}
        return Response({"message": "Fetched all products", "data": data, "status": "success"},
                        status=status.HTTP_200_OK)


class FavoriteProductsView(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user is None:
            return Response({"message": "User does not exist", "status": "failed"}, status=status.HTTP_400_BAD_REQUEST)
        favorite_products = FavoriteProduct.objects.filter(customer=user)

        data = [
            {
                "title": product.title,
                "slug": product.slug,
                "category": product.category.name,
                "description": product.description,
                "style": product.style,
                "price": product.price,
                "percentage_off": product.percentage_off,
                "size": product.size.values_list("name", flat=True),
                "colour": product.colour.values_list("name", flat=True),
                "ratings": product.ratings,
                "inventory": product.inventory,
                "flash_sale_start_date": product.flash_sale_start_date,
                "flash_sale_end_date": product.flash_sale_end_date,
                "condition": product.condition,
                "location": product.location.name,
                "discount_price": product.discount_price,
                "average_ratings": product.average_ratings,
                "images": [image.image_url for image in product.images.all()]
            } for product in favorite_products.all()
        ]
        return Response({"message": "All favorite products fetched", "data": data, "status": "success"},
                        status=status.HTTP_200_OK)

    def post(self, request):
        user = request.user
        product_id = request.data.get("product_id")
        if not product_id:
            return Response({"message": "Product id is required", "status": "failed"},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"message": "Invalid product id", "status": "failed"},
                            status=status.HTTP_400_BAD_REQUEST)

        favorite, created = FavoriteProduct.objects.get_or_create(customer=user, product=product)

        if created:
            return Response({"message": "Product added to favorites", "status": "success"},
                            status=status.HTTP_201_CREATED)
        else:
            return Response({"message": "Product already in favorites", "status": "success"}, status=status.HTTP_200_OK)

    def delete(self, request):
        user = request.user
        product_id = request.data.get("product_id")
        if not product_id:
            return Response({"message": "Product id is required", "status": "failed"},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"message": "Invalid product id", "status": "failed"},
                            status=status.HTTP_400_BAD_REQUEST)

        FavoriteProduct.objects.filter(customer=user, product=product).delete()
        return Response({"message": "Product removed from favorite list", "status": "succeed"},
                        status=status.HTTP_200_OK)


class ProductDetailView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProductDetailSerializer

    def get(self, request, *args, **kwargs):
        product_id = self.kwargs.get("product_id")
        if product_id is None:
            return Response({"message": "This field is required", "status": "succeed"},
                            status=status.HTTP_400_BAD_REQUEST)
        product = Product.categorized.filter(id=product_id)
        if not product.exists():
            return Response({"message": "This product does not exist, try again", "status": "failed"},
                            status=status.HTTP_400_BAD_REQUEST)
        product = product.get()
        related_products = product.category.products.exclude(id=product_id)[:10]
        product_serializer = self.serializer_class(product)
        related_products_serializer = ProductSerializer(related_products, many=True)
        product_reviews = product.product_reviews.select_related('customer')
        product_review_serializer = ProductReviewSerializer(product_reviews, many=True)
        return Response({"message": "Product successfully fetched",
                         "data": {
                             "product_details": product_serializer.data,
                             "related_products": related_products_serializer.data,
                             "product_reviews": product_review_serializer.data
                         }, "status": "succeed"}, status=status.HTTP_200_OK)


class AddProductReviewView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AddProductReviewSerializer

    def post(self, request):
        user = request.user
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        product_id = data.get('id')
        product = Product.categorized.get(id=product_id)
        images = request.FILES.getlist('images')
        if len(images) > 3:
            return Response({"message": "The maximum number of allowed images is 3"})
        product_review = ProductReview.objects.create(customer=user, product=product, **data)
        for image in images:
            ProductReviewImage.objects.create(product_review=product_review, image=image)
        return Response({"message": "Review created successfully", "status": "succeed"}, status.HTTP_201_CREATED)


class NotificationView(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.is_staff:
            notifications = Notification.objects.all().values('notification_type', 'title', 'description', 'created')
        else:
            notifications = Notification.objects.filter(Q(customers__in=[user]) | Q(general=True)).values(
                    'notification_type', 'title', 'customers', 'description', 'created')
        return Response({"message": "Notifications sent", "data": notifications, "status": "succeed"},
                        status.HTTP_200_OK)


class CategoryListView(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        all_categories = Category.objects.values('id', 'title')
        women_categories = Category.objects.filter(gender=GENDER_MALE).values('id', 'title')
        men_categories = Category.objects.filter(gender=GENDER_FEMALE).values('id', 'title')
        return Response({"message": "All categories fetched", "all_categories": all_categories,
                         "men_categories": men_categories, "women_categories": women_categories, "status": "succeed"},
                        status.HTTP_200_OK)


class ProductsFilterView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = ProductFilter
    search_fields = ['title', 'description']
    queryset = Product.categorized.all()

    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({"message": "All products fetched", "data": serializer.data, "status": "succeed"},
                        status.HTTP_200_OK)


class CartItemView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AddCartItemSerializer

    def get(self, request, *args, **kwargs):
        cart_id = request.query_params.get('cart_id', None)
        if not cart_id:
            return Response({"message": "Cart ID not provided."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            cart = Cart.objects.get(id=cart_id)
        except Cart.DoesNotExist:
            return Response({"message": "Cart not found", "status": "failed"},
                            status=status.HTTP_404_NOT_FOUND)
        serializer = CartItemSerializer(cart.items.all(), many=True)
        return Response({"message": "Cart Items fetched successfully", "data": serializer.data, "status": "succeed"},
                        status=status.HTTP_200_OK)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cart_item = serializer.save()

        # Serialize the cart item object to a dictionary
        cart_item_data = CartItemSerializer(cart_item).data
        return Response(
                {"message": "Cart item successfully added to the cart", "data": cart_item_data, "status": "succeed"},
                status=status.HTTP_201_CREATED)

    def patch(self, request):
        serializer = UpdateCartItemSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_cart_item = serializer.save()

        # Serialize the cart item object to a dictionary
        updated_cart_item_data = CartItemSerializer(updated_cart_item).data
        return Response(
                {"message": "Cart item updated successfully", "data": updated_cart_item_data, "status": "succeed"},
                status=status.HTTP_201_CREATED)

    def delete(self, request):
        serializer = DeleteCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Item deleted successfully.", "status": "succeed"},
                        status=status.HTTP_204_NO_CONTENT)