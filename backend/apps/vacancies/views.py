from django.db.models import Q
from django.utils import timezone
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny

from .models import Vacancy
from .serializers import VacancySerializer


def public_vacancies():
    now = timezone.now()
    return Vacancy.objects.filter(status=Vacancy.Status.PUBLISHED).filter(
        Q(closing_at__isnull=True) | Q(closing_at__gte=now)
    )


class VacancyListView(ListAPIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = VacancySerializer

    def get_queryset(self):
        return public_vacancies()


class VacancyDetailView(RetrieveAPIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = VacancySerializer
    lookup_field = "slug"

    def get_queryset(self):
        return public_vacancies()
