from rest_framework import viewsets,status,permissions,filters,parsers
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from .models import Job, JobApplication
from .serializers import JobSerializer, JobApplicationSerializer, JobApplicationCreateSerializer, JobCreateSerializer,JobApplicationApplySerializer
from .search import JobSearch
from apps.users.permissions import IsOwnerOrReadOnly

class JobViewSet(viewsets.ModelViewSet):
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'company__name', 'skills_required']
    filterset_fields = ['job_type', 'experience_level', 'location', 'is_remote']
    ordering_fields = ['created_at', 'salary_min', 'salary_max']
    ordering = ['-created_at']

    def perform_create(self, serializer):
        serializer.save(recruiter=self.request.user)
    def get_queryset(self):
        queryset = Job.objects.filter(is_active=True).select_related(
            'company', 'recruiter', 'recruiter__profile'
        )
        
        if self.action == 'list' and self.request.user.is_authenticated:
            # For recruiters, show their jobs including inactive ones
            if hasattr(self.request.user, 'is_recruiter') and self.request.user.is_recruiter:
                queryset = Job.objects.filter(recruiter=self.request.user)
        
        return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return JobCreateSerializer
        elif self.action == 'apply':
            return JobApplicationApplySerializer
        return JobSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsOwnerOrReadOnly()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(recruiter=self.request.user)

    @action(detail=False, methods=['get'])
    def search(self, request):
        """Advanced job search"""
        query = request.query_params.get('q', '')
        search_filters = {
            'location': request.query_params.get('location'),
            'job_type': request.query_params.getlist('job_type'),
            'experience_level': request.query_params.getlist('experience_level'),
            'is_remote': request.query_params.get('is_remote'),
            'salary_min': request.query_params.get('salary_min'),
            'salary_max': request.query_params.get('salary_max'),
        }
        
        jobs = JobSearch.search_jobs(query, search_filters)
        page = self.paginate_queryset(jobs)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(jobs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], parser_classes=[parsers.MultiPartParser, parsers.FormParser])
    def apply(self, request, pk=None):
        """Apply for a job"""
        job = self.get_object()
        
        if not job.is_active:
            return Response(
                {"error": "This job is no longer active"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if JobApplication.objects.filter(job=job, applicant=request.user).exists():
            return Response(
                {"error": "You have already applied for this job"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = JobApplicationApplySerializer(
            data=request.data,
            context={'request': request, 'job': job}
        )
        
        if serializer.is_valid():
            application = serializer.save()
            
            # Update application count
            job.application_count += 1
            job.save()
            
            # Create notification for recruiter
            from apps.notifications.models import Notification
            Notification.objects.create(
                user=job.recruiter,
                notification_type='job_application',
                actor=request.user,
                message=f"{request.user.first_name} applied for your job: {job.title}"
            )
            
            return_serializer = JobApplicationSerializer(application)
            return Response(return_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def recommendations(self, request):
        """Get job recommendations based on user profile"""
        user = request.user
        
        if not hasattr(user, 'profile'):
            return Response(
                {"error": "User profile not found. Please complete your profile to get job recommendations."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        profile = user.profile

        
        recommended_jobs = Job.objects.filter(is_active=True)
        
        if profile.location:
            recommended_jobs = recommended_jobs.filter(location__icontains=profile.location)
        
        if profile.skills:
            skills_list = [skill.strip() for skill in profile.skills.split(',')[:3]]
            skills_query = Q()
            for skill in skills_list:
                skills_query |= Q(skills_required__icontains=skill)
            recommended_jobs = recommended_jobs.filter(skills_query)
        
        recommended_jobs = recommended_jobs[:10]
        
        serializer = self.get_serializer(recommended_jobs, many=True)
        return Response(serializer.data)


class JobApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = JobApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.JSONParser, parsers.FormParser]


    def get_queryset(self):
        user = self.request.user
        
        if hasattr(user, 'is_recruiter') and user.is_recruiter:
            # Recruiters can see applications for their jobs
            return JobApplication.objects.filter(
                job__recruiter=user
            ).select_related('job', 'applicant', 'applicant__profile')
        else:
            # Job seekers can see their own applications
            return JobApplication.objects.filter(
                applicant=user
            ).select_related('job', 'job__company')
    def get_serializer_class(self, *args, **kwargs):
        if self.action == 'create':
            return JobApplicationCreateSerializer
        return JobApplicationSerializer
    def get_serializer_context(self):
        """Add request to serializer context"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update application status (for recruiters)"""
        application = self.get_object()
        
        if application.job.recruiter != request.user:
            return Response(
                {"error": "You can only update applications for your jobs"},
                status=status.HTTP_403_FORBIDDEN
            )

        new_status = request.data.get('status')
        if new_status not in dict(JobApplication.STATUS_CHOICES):
            return Response(
                {"error": "Invalid status"},
                status=status.HTTP_400_BAD_REQUEST
            )

        application.status = new_status
        application.save()

        # Create notification for applicant
        from apps.notifications.models import Notification
        Notification.objects.create(
            user=application.applicant,
            notification_type='job_application_update',
            actor=request.user,
            target_content_type='job_application',
            message=f"Your application for {application.job.title} has been {new_status}"
        )

        serializer = self.get_serializer(application)
        return Response(serializer.data)