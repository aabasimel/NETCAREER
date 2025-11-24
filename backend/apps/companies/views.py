from rest_framework import viewsets, status, permissions, filters, parsers
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count
from .models import Company
from .serializers import (
    CompanySerializer,
    CompanyCreateSerializer,
    CompanyUpdateSerializer,
    CompanyStatsSerializer,
)
from apps.users.permissions import IsOwnerOrReadOnly, IsEmployer


class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = [
        "name",
        "description",
        "website",
        "industry",
        "company_size",
        "founded_year",
        "headquarters",
        "specialities",
    ]
    filterset_fields = [
        "name",
        "description",
        "website",
        "industry",
        "company_size",
        "founded_year",
        "headquarters",
        "specialities",
    ]
    parser_classes = [parsers.MultiPartParser, parsers.JSONParser, parsers.FormParser]

    def get_parser_context(self, http_request):
        """
        Override to ensure proper file handling
        """
        context = super().get_parser_context(http_request)
        context["request"] = self.request
        return context

    def get_permissions(self):
        if self.action == "create":
            permission_classes = [permissions.IsAuthenticated, IsEmployer]
        else:
            permission_classes = [IsOwnerOrReadOnly]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def perform_update(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=False, methods=["get"])
    def my_companies(self, request):
        """Get companies owned by the current employer"""
        companies = Company.objects.filter(owner=request.user)
        serializer = self.get_serializer(companies, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def stats(self, request, pk=None):
        """Get company statistics"""
        company = self.get_object()

        # Check if user is owner or admin
        if not (request.user == company.owner or request.user.is_admin()):
            return Response(
                {"error": "Only company owners and admins can view stats"},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = CompanyStatsSerializer(company)
        return Response(serializer.data)
