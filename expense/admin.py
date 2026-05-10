from django.contrib import admin
from .models import CustomUser as User, Category, Expense

# Register your models here.
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'phone')
    search_fields = ('username', 'email', 'phone')


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'category', 'amount', 'description', 'date')
    search_fields = ('user__username', 'category__name', 'description')
    list_filter = ('category', 'date')

admin.site.register(User, UserAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Expense, ExpenseAdmin)
