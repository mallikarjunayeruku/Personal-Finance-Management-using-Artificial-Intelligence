
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import CategoryViewSet
from .views_plaid import CreatePlaidLinkTokenView, ExchangePublicTokenView
from .views_webhook import PlaidWebhookView

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
router.register(r"categories", CategoryViewSet, basename="categories")
urlpatterns = [ path('', include(router.urls)),
                path("plaid/link-token/", CreatePlaidLinkTokenView.as_view(), name="plaid-link-token"),
                path("plaid/exchange-public-token/", ExchangePublicTokenView.as_view(),
                     name="plaid-exchange-public-token"),
                path("plaid/webhook/", PlaidWebhookView.as_view(), name="plaid-webhook"),

                ]
