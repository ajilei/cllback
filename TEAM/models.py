from django.db import models


class TeamModel(models.Model):
    name = models.CharField('uid', null=True, blank=True, max_length=50, db_column='name')
    parent = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='组',
        related_name='children',  db_constraint=False
    )
    is_deleted = models.BooleanField('是否删除', default=False, null=True, blank=True,db_column='is_deleted')
    class Meta:
        db_table = "team"