from django.db import models


# This class is use for create the cause model
class Cause(models.Model):
    id = models.IntegerField(default=False, null=False, primary_key=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    image = models.CharField(max_length=500, blank=True, null=True)
    color = models.CharField(max_length=500, blank=True, null=True)
    color_gradient = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.IntegerField(default=1, null=False)
    is_verified = models.IntegerField(default=1, null=False)
    is_deleted = models.IntegerField(default=0, null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'causes'


# This class is use for create the sub-cause model
class SubCause(models.Model):
    id = models.IntegerField(default=False, null=False, primary_key=True)
    causes = models.ForeignKey(Cause, related_name='causes_id', on_delete=models.CASCADE)
    name = models.CharField(max_length=255, blank=True, null=True)
    image = models.CharField(max_length=500, blank=True, null=True)
    color = models.CharField(max_length=500, blank=True, null=True)
    color_gradient = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.IntegerField(default=1, null=False)
    is_verified = models.IntegerField(default=1, null=False)
    is_deleted = models.IntegerField(default=0, null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'sub_causes'
