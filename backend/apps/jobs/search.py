from django.db.models import Q

from .models import Job


class JobSearch:
    @staticmethod
    def search_jobs(query=None, filters=None):
        queryset = Job.objects.filter(is_active=True)

        if query:
            queryset = queryset.filter(
                Q(title__icontains=query)
                | Q(description__icontains=query)
                | Q(company__name__icontains=query)
                | Q(skills_required__icontains=query)
            )

        if filters:
            if filters.get("location"):
                queryset = queryset.filter(location__icontains=filters["location"])
            if filters.get("job_type"):
                queryset = queryset.filter(job_type__in=filters["job_type"])
            if filters.get("experience_level"):
                queryset = queryset.filter(
                    experience_level__in=filters["experience_level"]
                )
            if filters.get("is_remote"):
                queryset = queryset.filter(is_remote=filters["is_remote"])
            if filters.get("salary_min"):
                queryset = queryset.filter(salary_min__gte=filters["salary_min"])
            if filters.get("salary_max"):
                queryset = queryset.filter(salary_max__lte=filters["salary_max"])

        return queryset.select_related("company", "recruiter")
