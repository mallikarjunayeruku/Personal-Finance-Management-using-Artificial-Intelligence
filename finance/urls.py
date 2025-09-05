
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
router = DefaultRouter()
router.register(r'bills', views.BillsViewSet)
router.register(r'paidmonths', views.PaidMonthsViewSet)
router.register(r'recursive-transactions', views.RecursiveTransactionsViewSet)
router.register(r'transactions', views.TransactionsViewSet)
router.register(r'goals', views.GoalViewSet)
router.register(r'achieved', views.AchievedViewSet)
router.register(r'budgets', views.BudgetViewSet)
router.register(r'accounts', views.AccountViewSet)
router.register(r'account-balances', views.AccountBalancesViewSet)
router.register(r'balances', views.BalancesViewSet)
router.register(r'assets', views.AssetViewSet)
router.register(r'premium', views.PremiumViewSet)
router.register(r'devices', views.DevicesViewSet)
router.register(r'login-info', views.LoginInformationViewSet)
router.register(r'feedback', views.FeedBackViewSet)
urlpatterns = [ path('', include(router.urls)), ]
