
from django.contrib import admin
from . import models
for m in [models.Bills, models.PaidMonths, models.RecursiveTransactions, models.Transactions,
          models.Goal, models.Achieved, models.Budget, models.Account, models.AccountBalances,
          models.Balances, models.Asset, models.Premium, models.Devices, models.LoginInformation,
          models.FeedBack]:
    @admin.register(m)
    class ModelAdmin(admin.ModelAdmin):
        list_display = tuple([f.name for f in m._meta.fields][:6])
        search_fields = ('id',)
        list_filter = tuple([f.name for f in m._meta.fields if f.get_internal_type() in ('BooleanField','CharField','IntegerField')][:4])
