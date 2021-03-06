from django.contrib import admin
import directory.models as models


class ResAdmin(admin.ModelAdmin):
    list_filter = ('podrazdeleniye', 'groups', 'hide')
    list_display = ('title', 'podrazdeleniye',)
    list_display_links = ('title',)


class RefAdmin(admin.ModelAdmin):
    list_filter = ('fraction',)
    list_display = ('title', 'fraction', 'ref_m', 'ref_f', 'about')
    list_display_links = ('title',)


admin.site.register(models.ResearchGroup)
admin.site.register(models.Researches, ResAdmin)
admin.site.register(models.ParaclinicInputGroups)
admin.site.register(models.ParaclinicInputField)
admin.site.register(models.References, RefAdmin)
admin.site.register(models.ResultVariants)
admin.site.register(models.MaterialVariants)
admin.site.register(models.Fractions)
admin.site.register(models.Absorption)
admin.site.register(models.ReleationsFT)
admin.site.register(models.AutoAdd)
