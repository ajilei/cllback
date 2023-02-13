from django.db import models


class JobOrderModel(models.Model):
    jobTitle = models.CharField('jobTitle', null=True, blank=True, max_length=518, db_column='jobTitle')

    class Meta:
        db_table = "joborder"
