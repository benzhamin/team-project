from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter




from .views import (
    RegisterUserView,
    LoginUserView,
    LogoutUserView,
    PatientProfileAPIView,
    DoctorProfileAPIView,
    SpecializationViewSet,
    ReviewViewSet,
)

# Authentication-related URLs
auth_urls = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', RegisterUserView.as_view(), name='register'),
    path('login/', LoginUserView.as_view(), name='login'),
    path('logout/', LogoutUserView.as_view(), name='logout'),
]

# Profile-related URLs
profile_urls = [
    path('profile/patient/', PatientProfileAPIView.as_view(), name='patient-profile'),
    path('profile/doctor/', DoctorProfileAPIView.as_view(), name='doctor-profile'),
]

# Specialization-related URLs
router = DefaultRouter()
router.register(r'specializations', SpecializationViewSet, basename='specialization')
router.register(r'reviews', ReviewViewSet, basename='review')

# Combine all groups into the main urlpatterns
urlpatterns = [
    path('auth/', include(auth_urls)),  # Grouped under 'auth/'
    path('', include(profile_urls)),   # Profile endpoints at the root
    path('', include(router.urls)),  # Specialization endpoints at the root
]