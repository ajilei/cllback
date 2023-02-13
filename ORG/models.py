from django.db import models


class TitleModel(models.Model):

    name = models.CharField('title', null=True, blank=True, max_length=518, db_column='name')

    class Meta:
        db_table = "title"
class UrlModel(models.Model):
    name = models.CharField('title', null=True, blank=True, max_length=518, db_column='name')
    url = models.CharField('title', null=True, blank=True, max_length=518, db_column='url')
    text = models.CharField('title', null=True, blank=True, max_length=518, db_column='text')
    params = models.CharField('title', null=True, blank=True, max_length=518, db_column='params')
    status = models.CharField('title', null=True, blank=True, max_length=518, db_column='fun')
    class Meta:
        db_table = "url"

