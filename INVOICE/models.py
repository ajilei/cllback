from django.db import models
from USER.models import UserModel

class InvoiceModel(models.Model):
    description = models.CharField('pay_note', null=True, blank=True, max_length=518, db_column='pay_note')
    status = models.CharField('status', null=True, blank=True, max_length=518, db_column='status')
    appStatus= models.CharField('appstatus', null=True, blank=True, max_length=518, db_column='_approval_status')
    active = models.CharField('active', null=True, blank=True, max_length=518, db_column='active')
    invoiceAmount = models.FloatField('invoiceAmount', null=True, blank=True, db_column='invoiceAmount')
    created = models.DateTimeField( null=True, db_column='dateAdded')
    #核算时间
    time2 = models.DateTimeField( null=True, db_column='gllueext_AccountedRevenueDate')
    time3 = models.DateTimeField( null=True, db_column='gllueext_AccountedPaymentReceivedDate')
    feeCharge = models.FloatField('feeCharge', null=True, blank=True)
    invoiceAmount = models.FloatField('invoiceAmount', null=True, blank=True)
    paymentReceived = models.FloatField('paymentReceived', null=True, blank=True)
    class Meta:
        db_table = "invoice"


class MoneyClientModel(models.Model):
    revenue = models.FloatField('revenue', null=True, blank=True, db_column='revenue')
    user = models.ForeignKey(
        'USER.UserModel', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='组',
         db_constraint=False
    )
    invoice = models.ForeignKey(
        'INVOICE.InvoiceModel', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='组',
        related_name='invoice_id', db_constraint=False
    )
    team = models.ForeignKey(
        'TEAM.TeamModel', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='所属团队',
         db_constraint=False,db_column='belong_team_id',
    )
    class Meta:
        db_table = "invoiceassignment"
