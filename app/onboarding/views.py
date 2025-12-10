
from django.utils.translation import gettext_lazy as _

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import FileUploadParser
from rest_framework.parsers import MultiPartParser
from rest_framework import serializers

from business import models as business_models
from business import serializers as business_serializers
from business.utils import registry as business_registry


from onboarding import models as onboarding_models
from onboarding import serializers as onboarding_serializers


from user.permissions import IsOwner


class FreelancerCreateView(generics.CreateAPIView):
    """
    API view to create a new freelancer.
    """
    serializer_class = onboarding_serializers.FreelancerCreateSerializer
    permission_classes = [IsAuthenticated]


class FreelancerUpdateView(generics.UpdateAPIView):
    """
    API view to update an existing freelancer.
    """
    serializer_class = onboarding_serializers.FreelancerUpdateSerializer
    permission_classes = [IsAuthenticated, IsOwner]
    allowed_methods = ["PATCH",]
    lookup_field = "uid"
    queryset = onboarding_models.FreeLancer.objects.all()


class FreelancerDetailView(generics.RetrieveAPIView):
    """
    API view to retrieve a freelancer.
    """
    queryset = onboarding_models.FreeLancer.objects.all()
    serializer_class = onboarding_serializers.FreelancerDetailSerializer
    permission_classes = [IsAuthenticated, IsOwner]
    
    def get_object(self):
        user = self.request.user
        return user.freelancer


class FreelancerDetailWithUidView(generics.RetrieveAPIView):
    """
    API view to retrieve a freelancer by UID.
    """
    queryset = onboarding_models.FreeLancer.objects.all()
    serializer_class = onboarding_serializers.FreelancerDetailSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.get_queryset().get(uid=self.kwargs["uid"])


class FreelancerDeleteView(generics.DestroyAPIView):
    """
    API view to delete a freelancer.
    """
    permission_classes = [IsAuthenticated, IsOwner]
    queryset = onboarding_models.FreeLancer.objects.all()
    
    def get_object(self):
        user = self.request.user
        return user.freelancer
    
    def delete(self, request, *args, **kwargs):
        business_models.Business.objects.filter(
            user=request.user,
        ).delete()
        return super().delete(request, *args, **kwargs)


class CostumerCreateView(generics.CreateAPIView):
    """
    API view to create a new costumer.
    """
    serializer_class = onboarding_serializers.CostumerCreateSerializer
    permission_classes = [IsAuthenticated]



class CostumerDetailView(generics.RetrieveAPIView):
    """
    API view to retrieve a costumer.
    """
    queryset = onboarding_models.Costumer.objects.all()
    serializer_class = onboarding_serializers.CostumerDetailSerializer
    permission_classes = [IsAuthenticated, IsOwner]
    

    def get_object(self):
        user = self.request.user
        return user.costumer


class CostumerUpdateView(generics.UpdateAPIView):
    """
    API view to update an existing costumer.
    """
    queryset = onboarding_models.Costumer.objects.all()
    serializer_class = onboarding_serializers.CostumerUpdateSerializer
    permission_classes = [IsAuthenticated]
    allowed_methods = ["PATCH",]
    lookup_field = "uid"


class CostumerDeleteView(generics.DestroyAPIView):
    """
    API view to delete a costumer.
    """
    permission_classes = [IsAuthenticated, IsOwner]
    queryset = onboarding_models.Costumer.objects.all()
    
    def get_object(self):
        user = self.request.user
        return user.costumer



class BusinessCreateView(generics.CreateAPIView):
    """
    API view to create a new business.
    """
    serializer_class = onboarding_serializers.BusinessCreateSerializer
    permission_classes = [IsAuthenticated]


class MyBusinessView(generics.ListAPIView):
    """
    API view to retrieve the business of the authenticated user.
    """
    serializer_class = business_serializers.BusinessListSerializer
    queryset = business_models.Business.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return business_registry.BusinessRegistry.get_annotated_business(
           user=self.request.user,
        ).filter(
            user=self.request.user,
        )

class BusinessUpdateView(generics.UpdateAPIView):
    """
    API view to update an existing business.
    """
    queryset = business_models.Business.objects.all()
    serializer_class = onboarding_serializers.BusinessUpdateSerializer
    permission_classes = [IsAuthenticated, IsOwner]
    allowed_methods = ["PATCH",]
    lookup_field = "uid"


class BusinessDeleteView(generics.DestroyAPIView):
    """
    API view to delete a business.
    """
    permission_classes = [IsAuthenticated, IsOwner]
    queryset = business_models.Business.objects.all()
    lookup_field = "uid"
    
    def get_object(self):
        return business_models.Business.objects.filter(
            user=self.request.user,
            uid=self.kwargs["uid"],
        ).first()


class WorkingHoursCreateView(generics.CreateAPIView):
    """
    API view to create a new working hours.
    """
    serializer_class = onboarding_serializers.WorkingHoursCreateSerializer
    permission_classes = [IsAuthenticated]


class BreakingHoursCreateView(generics.CreateAPIView):
    """
    API view to create a new breaking hours.
    """
    serializer_class = onboarding_serializers.BreakingHoursCreateSerializer
    permission_classes = [IsAuthenticated]


class WorkingHoursDeleteView(generics.CreateAPIView):
    """
    API view to delete a working hours.
    """
    serializer_class = onboarding_serializers.WorkingHoursDeleteSerializer
    permission_classes = [IsAuthenticated]


class BreakingHoursDeleteView(generics.CreateAPIView):
    """
    API view to delete a breaking hours.
    """
    serializer_class = onboarding_serializers.BreakingHoursDeleteSerializer
    permission_classes = [IsAuthenticated]



class SocialCreateView(generics.CreateAPIView):
    """
    API view to create a new social.
    """
    serializer_class = onboarding_serializers.SocialCreateSerializer
    permission_classes = [IsAuthenticated]


class SocialDeleteView(generics.DestroyAPIView):
    """
    API view to delete a social.
    """
    serializer_class = onboarding_serializers.SocialCreateSerializer
    permission_classes = [IsAuthenticated]
    queryset = business_models.SocialMedia.objects.all()
    lookup_field = "uid"


class UploadImageView(generics.CreateAPIView):

    parser_classes = [MultiPartParser, FileUploadParser]
    serializer_class = onboarding_serializers.UploadImageSerializer
    permission_classes = [IsAuthenticated]


class DeleteImageView(generics.DestroyAPIView):
    """
    API view to delete an image.
    """
    permission_classes = [IsAuthenticated]
    queryset = business_models.Gallery.objects.all()
    lookup_field = "uid"


class UploadVideoView(generics.CreateAPIView):
    """
    API view to upload a video.
    """
    parser_classes = [MultiPartParser, FileUploadParser]
    serializer_class = onboarding_serializers.UploadVideoSerializer
    permission_classes = [IsAuthenticated]


class DeleteVideoView(generics.DestroyAPIView):
    """
    API view to delete a video.
    """
    permission_classes = [IsAuthenticated]
    queryset = business_models.VideoGallery.objects.all()
    lookup_field = "uid"


class ServiceCreateView(generics.CreateAPIView):
    """
    API view to create a new service.
    """
    serializer_class = onboarding_serializers.ServiceCreateSerializer
    parser_classes = [MultiPartParser, FileUploadParser]
    permission_classes = [IsAuthenticated]


class ServiceUpdateView(generics.UpdateAPIView):
    """
    API view to update an existing service.
    """
    serializer_class = onboarding_serializers.ServiceUpdateSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FileUploadParser]
    allowed_methods = ["PATCH",]
    lookup_field = "uid"
    queryset = business_models.Service.objects.all()


class UploadImageServiceView(generics.CreateAPIView):
    parser_classes = [MultiPartParser, FileUploadParser]
    serializer_class = onboarding_serializers.UploadImageServiceSerializer
    permission_classes = [IsAuthenticated]


class WorkingHoursCreateServiceView(generics.CreateAPIView):
    """
    API view to create a new working hours for a service.
    """
    serializer_class = onboarding_serializers.WorkingHoursCreateServiceSerializer
    permission_classes = [IsAuthenticated]
    

class ServiceDeleteView(generics.DestroyAPIView):
    """
    API view to delete a service.
    """
    permission_classes = [IsAuthenticated]
    queryset = business_models.Service.objects.all()
    lookup_field = "uid"


class EmployeeCreateView(generics.CreateAPIView):
    """
    API view to create a new employee.
    """
    serializer_class = onboarding_serializers.EmployeeCreateSerializer
    parser_classes = [MultiPartParser, FileUploadParser]
    permission_classes = [IsAuthenticated]


class FreelancerToEmployeeView(generics.CreateAPIView):
    """
    API view to convert a freelancer to an employee.
    """
    serializer_class = onboarding_serializers.FreelancerToEmployeeSerializer
    permission_classes = [IsAuthenticated]
    queryset = onboarding_models.FreeLancer.objects.all()


class FreelancerApplyView(generics.CreateAPIView):
    """
    API view to apply a freelancer to a business.
    """
    serializer_class = onboarding_serializers.FreelancerApplySerializer
    permission_classes = [IsAuthenticated]


class FreelancerApplyListView(generics.ListAPIView):
    """
    API view to list all freelancer applications for a business.
    """
    serializer_class = onboarding_serializers.FreelancerApplyListSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        freelancer_uid = self.kwargs["freelancer_uid"]
        return onboarding_models.FreelancerBusinessApply.objects.filter(
            freelancer__uid=freelancer_uid,
        ).prefetch_related(
            "business",
        ).distinct()


class FreelancerApplyBusinessListView(generics.ListAPIView):
    """
    API view to list all freelancer applications for a business.
    """
    serializer_class = onboarding_serializers.FreelancerApplyListSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        business_uid = self.kwargs["business_uid"]
        return onboarding_models.FreelancerBusinessApply.objects.filter(
            business__uid=business_uid,
        ).prefetch_related(
            "freelancer",
        ).distinct()
    

class FreelancerApplyUpdateView(generics.UpdateAPIView):
    """
    API view to update a freelancer application.
    """
    serializer_class = onboarding_serializers.FreelancerApplyUpdateSerializer
    permission_classes = [IsAuthenticated]
    allowed_methods = ["PATCH",]
    lookup_field = "uid"
    queryset = onboarding_models.FreelancerBusinessApply.objects.all()


class FreelancerApplyDeleteView(generics.DestroyAPIView):
    """
    API view to delete a freelancer application.
    """
    permission_classes = [IsAuthenticated]
    queryset = onboarding_models.FreelancerBusinessApply.objects.all()
    lookup_field = "uid"


class FreelancerLeaveView(generics.DestroyAPIView):
    """
    API view to delete a freelancer.
    """
    permission_classes = [IsAuthenticated]
    queryset = onboarding_models.FreeLancer.objects.all()
    
    def get_object(self):
        user = self.request.user
        
        if not user.freelancer:
            raise serializers.ValidationError(_("User is not a freelancer."))
        if not user.freelancer.employee:
            raise serializers.ValidationError(_("Freelancer does not have an employee profile."))
        
        return user.freelancer.employee


class EmployeeUpdateView(generics.UpdateAPIView):
    """
    API view to update an existing employee.
    """
    serializer_class = onboarding_serializers.EmployeeUpdateSerializer
    permission_classes = [IsAuthenticated]
    allowed_methods = ["PATCH",]
    lookup_field = "uid"
    queryset = business_models.Employee.objects.all()


class EmployeeDeleteView(generics.DestroyAPIView):
    """
    API view to delete an employee.
    """
    permission_classes = [IsAuthenticated]
    queryset = business_models.Employee.objects.all()
    lookup_field = "uid"


class WorkingHoursCreateEmployeeView(generics.CreateAPIView):
    """
    API view to create a new working hours for an employee.
    """
    serializer_class = onboarding_serializers.WorkingHoursCreateEmployeeSerializer
    permission_classes = [IsAuthenticated]

