
from django.conf import settings
from django.db import models

class RepeatBills(models.TextChoices):
    ONE_TIME_ONLY = 'ONE_TIME_ONLY', 'One time only'
    WEEKLY = 'WEEKLY', 'Weekly'
    MONTHLY = 'MONTHLY', 'Monthly'
    EVERY_SIX_MONTHS = 'EVERY_SIX_MONTHS', 'Every six months'
    YEARLY = 'YEARLY', 'Yearly'

class RepeatTransaction(models.TextChoices):
    DAILY = 'DAILY', 'Daily'
    WEEKLY = 'WEEKLY', 'Weekly'
    MONTHLY = 'MONTHLY', 'Monthly'
    EVERY_3_MONTHS = 'EVERY_3_MONTHS', 'Every 3 months'
    EVERY_6_MONTHS = 'EVERY_6_MONTHS', 'Every 6 months'
    YEARLY = 'YEARLY', 'Yearly'
    NONE = 'NONE', 'None'

class OwnedModel(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="%(class)ss")
    ownerId = models.CharField(max_length=64, blank=True, null=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: abstract = True

class Bills(OwnedModel):
    title = models.CharField(max_length=255, blank=True, null=True)
    amount = models.FloatField(blank=True, null=True)
    repeat = models.CharField(max_length=32, choices=RepeatBills.choices, blank=True, null=True)
    category = models.CharField(max_length=120, blank=True, null=True)
    cancelled = models.BooleanField(default=False)
    dueDate = models.DateTimeField(blank=True, null=True, db_index=True)
    lastPaidDate = models.DateTimeField(blank=True, null=True)
    lastPaidDueDate = models.DateTimeField(blank=True, null=True)

class PaidMonths(OwnedModel):
    paidMonth = models.DateTimeField(blank=True, null=True)
    accountId = models.CharField(max_length=64, blank=True, null=True)
    bills = models.ForeignKey(Bills, on_delete=models.CASCADE, related_name='paidMonths', db_index=True)

class RecursiveTransactions(OwnedModel):
    sourceId = models.CharField(max_length=64, blank=True, null=True)
    tableName = models.CharField(max_length=64, blank=True, null=True)
    repeat = models.CharField(max_length=32, choices=RepeatTransaction.choices, blank=True, null=True)
    recursiveUpdatedDate = models.DateTimeField(blank=True, null=True)

class Goal(OwnedModel):
    goalName = models.CharField(max_length=120, blank=True, null=True)
    goalDesc = models.TextField(blank=True, null=True)
    goalType = models.CharField(max_length=64, blank=True, null=True)
    amount = models.FloatField(blank=True, null=True)
    savedAmount = models.FloatField(blank=True, null=True, default=0)
    duration = models.IntegerField(blank=True, null=True)
    goalCategory = models.IntegerField(blank=True, null=True)
    createdDate = models.DateTimeField(blank=True, null=True)
    updatedDate = models.DateTimeField(blank=True, null=True)
    notification = models.CharField(max_length=255, blank=True, null=True)
    isCompleted = models.BooleanField(default=False)
    uniqueId = models.CharField(max_length=64, blank=True, null=True)

class Achieved(OwnedModel):
    owner_id = models.CharField(max_length=64, blank=True, null=True)
    amount = models.FloatField(blank=True, null=True)
    achievedDate = models.DateTimeField(blank=True, null=True)
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name='achievedGoals', db_index=True)

class Budget(OwnedModel):
    owner_id = models.CharField(max_length=64, blank=True, null=True)
    type = models.IntegerField(blank=True, null=True)
    untitledfield = models.CharField(max_length=255, blank=True, null=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    createdDate = models.DateTimeField(blank=True, null=True)
    updatedDate = models.DateTimeField(blank=True, null=True)
    amount = models.FloatField(blank=True, null=True)
    note = models.TextField(blank=True, null=True)

class Account(OwnedModel):
    isInternalAccount = models.BooleanField(default=False)
    accountId = models.CharField(max_length=64, blank=True, null=True, db_index=True)
    accountType = models.CharField(max_length=64, blank=True, null=True)
    subAccountType = models.CharField(max_length=64, blank=True, null=True)
    accountNumber = models.CharField(max_length=64, blank=True, null=True)
    accountName = models.CharField(max_length=255, blank=True, null=True)
    officialAccountName = models.CharField(max_length=255, blank=True, null=True)
    availableBalance = models.FloatField(blank=True, null=True, default=0)
    currentBalance = models.FloatField(blank=True, null=True, default=0)
    createdDate = models.DateTimeField(blank=True, null=True)
    updatedDate = models.DateTimeField(blank=True, null=True)
    transactionsUpdatedDate = models.DateTimeField(blank=True, null=True)
    balancedUpdatedDate = models.DateTimeField(blank=True, null=True)
    icon = models.IntegerField(blank=True, null=True)
    isoCurrencyCode = models.CharField(max_length=16, blank=True, null=True)
    unofficialCurrencyCode = models.CharField(max_length=16, blank=True, null=True)
    limit = models.FloatField(blank=True, null=True)
    loans = models.FloatField(blank=True, null=True)
    depts = models.FloatField(blank=True, null=True)

class Transactions(OwnedModel):
    ownerId_str = models.CharField(max_length=64, blank=True, null=True)
    amount = models.FloatField(blank=True, null=True)
    category = models.CharField(max_length=120, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    merchantName = models.CharField(max_length=255, blank=True, null=True)
    currencyCode = models.CharField(max_length=16, blank=True, null=True)
    checkNumber = models.CharField(max_length=64, blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    createdDate = models.DateTimeField(blank=True, null=True)
    transactionDate = models.DateTimeField(blank=True, null=True, db_index=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    path = models.CharField(max_length=255, blank=True, null=True)
    isIncome = models.BooleanField(default=False)
    repeat = models.CharField(max_length=32, choices=RepeatTransaction.choices, blank=True, null=True)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='transactions', db_index=True)
    isCashAccount = models.BooleanField(default=False)
    canDelete = models.BooleanField(default=True)

class AccountBalances(OwnedModel):
    income = models.FloatField(blank=True, null=True, default=0)
    expanses = models.FloatField(blank=True, null=True, default=0)
    balance = models.FloatField(blank=True, null=True, default=0)
    balanceMonth = models.CharField(max_length=32)
    balancedUpdatedDate = models.DateTimeField(blank=True, null=True)
    account = models.OneToOneField(Account, on_delete=models.SET_NULL, null=True, blank=True)

class Balances(OwnedModel):
    accountId = models.CharField(max_length=64, blank=True, null=True)
    available = models.FloatField(blank=True, null=True, default=0)
    current = models.FloatField(blank=True, null=True, default=0)
    limit = models.FloatField(blank=True, null=True, default=0)
    createdDate = models.DateTimeField(blank=True, null=True)
    updatedDate = models.DateTimeField(blank=True, null=True)
    accountBalances = models.OneToOneField(AccountBalances, on_delete=models.SET_NULL, null=True, blank=True)

class Asset(OwnedModel):
    name = models.CharField(max_length=255, blank=True, null=True)
    value = models.FloatField(blank=True, null=True, default=0)
    income = models.FloatField(blank=True, null=True, default=0)
    location = models.CharField(max_length=255, blank=True, null=True)
    lattitude = models.FloatField(blank=True, null=True)
    longnitude = models.FloatField(blank=True, null=True)
    path = models.CharField(max_length=255, blank=True, null=True)
    createdDate = models.DateTimeField(blank=True, null=True)
    updatedDate = models.DateTimeField(blank=True, null=True)
    addRevenueToAccount = models.BooleanField(default=False)
    repeat = models.CharField(max_length=32, choices=RepeatTransaction.choices, blank=True, null=True)

class Premium(OwnedModel):
    messageFromGooglePlay = models.TextField(blank=True, null=True)
    planIdentifier = models.CharField(max_length=64, blank=True, null=True)
    offeringIdentifier = models.CharField(max_length=64, blank=True, null=True)
    productTitle = models.CharField(max_length=255, blank=True, null=True)
    price = models.CharField(max_length=32, blank=True, null=True)
    priceCost = models.CharField(max_length=32, blank=True, null=True)
    currencyCode = models.CharField(max_length=16, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    purchaseDate = models.DateTimeField(blank=True, null=True)
    isActive = models.BooleanField(default=False)
    billingIssueDetectedAt = models.CharField(max_length=64, blank=True, null=True)
    expirationDate = models.CharField(max_length=64, blank=True, null=True)
    isSandbox = models.BooleanField(default=False)
    latestPurchaseDate = models.CharField(max_length=64, blank=True, null=True)
    originalPurchaseDate = models.CharField(max_length=64, blank=True, null=True)
    periodTypeName = models.CharField(max_length=64, blank=True, null=True)
    periodTypeIndex = models.IntegerField(blank=True, null=True)
    productIdentifier = models.CharField(max_length=64, blank=True, null=True)
    unsubscribeDetectedAt = models.CharField(max_length=64, blank=True, null=True)
    willRenew = models.BooleanField(default=False)
    plan = models.CharField(max_length=64, blank=True, null=True)
    premiumStartDate = models.CharField(max_length=64, blank=True, null=True)
    premiumEndDate = models.CharField(max_length=64, blank=True, null=True)
    isPremium = models.BooleanField(default=False)
    isExpired = models.BooleanField(default=False)

class Devices(OwnedModel):
    brand = models.CharField(max_length=64, blank=True, null=True)
    deviceName = models.CharField(max_length=120, blank=True, null=True)
    display = models.CharField(max_length=120, blank=True, null=True)
    fcmToken = models.CharField(max_length=255, blank=True, null=True)
    host = models.CharField(max_length=120, blank=True, null=True)
    hostId = models.CharField(max_length=120, blank=True, null=True)
    loginDate = models.CharField(max_length=64, blank=True, null=True)
    creationDate = models.CharField(max_length=64, blank=True, null=True)
    manufacturer = models.CharField(max_length=120, blank=True, null=True)
    model = models.CharField(max_length=120, blank=True, null=True)
    androidVersion = models.CharField(max_length=64, blank=True, null=True)
    isLoggedIn = models.BooleanField(default=False)
    isBiometricAuthEnabled = models.BooleanField(default=False)
    deviceId = models.CharField(max_length=120, blank=True, null=True)

class LoginInformation(OwnedModel):
    address = models.CharField(max_length=255, blank=True, null=True)
    latitude = models.CharField(max_length=64, blank=True, null=True)
    longitude = models.CharField(max_length=64, blank=True, null=True)
    loginDate = models.DateTimeField(blank=True, null=True)
    devices = models.ForeignKey(Devices, on_delete=models.CASCADE, related_name='LoginInformations', db_index=True)

class FeedBack(OwnedModel):
    feedBackVersion = models.CharField(max_length=64, blank=True, null=True)
    package = models.CharField(max_length=64, blank=True, null=True)
    buildNumber = models.CharField(max_length=64, blank=True, null=True)
    feedback = models.TextField(blank=True, null=True)
    createdDate = models.DateField(blank=True, null=True)
    tags = models.CharField(max_length=255, blank=True, null=True)
    userId = models.CharField(max_length=64, blank=True, null=True)
    user = models.CharField(max_length=64, blank=True, null=True)
    rating = models.IntegerField(blank=True, null=True)
