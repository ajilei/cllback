from django.db import models

# Create your models here.
class UserModel(models.Model):
    uid = models.CharField('uid', null=True, blank=True, max_length=50, db_column='uid')
    name = models.CharField('name', null=True, blank=True, max_length=50, db_column='englishName')
    chineseName = models.CharField('name', null=True, blank=True, max_length=50, db_column='chineseName')
    status = models.CharField('status', null=True, blank=True, max_length=50, db_column='status')
    email = models.CharField('邮箱', max_length=256, null=True, blank=True, db_column='email')
    mobile = models.CharField('手机', max_length=256, null=True, blank=True, db_column='mobile')
    joinDate = models.DateField( null=True, db_column='joinInDate')
    leaveDate = models.DateField(null=True, db_column='leaveDate')
    isleader = models.CharField( max_length=256, null=True, blank=True, db_column='isleader')
    role = models.CharField( max_length=256, null=True, blank=True, db_column='role')
    team = models.ForeignKey(
        'TEAM.TeamModel', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='组',
        related_name='team_id', db_constraint=False
    )
    title = models.ForeignKey(
        'ORG.TitleModel', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='职位',
        related_name='title_id', db_constraint=False
    )
    class Meta:
        db_table = "user"
