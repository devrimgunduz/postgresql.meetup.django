from django.contrib import admin
from .models import Language, Meetup, MeetupTranslation, Talk, TalkTranslation


class MeetupTranslationInline(admin.TabularInline):
    model  = MeetupTranslation
    extra  = 0
    fields = ('lang', 'field', 'value')


class TalkTranslationInline(admin.TabularInline):
    model  = TalkTranslation
    extra  = 0
    fields = ('lang', 'field', 'value')


class TalkInline(admin.StackedInline):
    model  = Talk
    extra  = 0
    fields = ('sort_order', 'speaker_name', 'speaker_photo', 'talk_duration_min')
    show_change_link = True


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display  = ('code', 'label', 'is_default', 'is_active', 'sort_order')
    list_editable = ('is_active', 'sort_order')
    ordering      = ('sort_order',)


@admin.register(Meetup)
class MeetupAdmin(admin.ModelAdmin):
    list_display  = ('__str__', 'status', 'event_date', 'updated_at')
    list_filter   = ('status',)
    list_editable = ('status',)
    inlines       = [MeetupTranslationInline, TalkInline]
    fieldsets = [
        (None, {'fields': ('status', 'event_date')}),
        ('Venue', {'fields': ('venue_address', 'venue_map_url')}),
        ('Registration', {'fields': ('registration_url',)}),
    ]


@admin.register(Talk)
class TalkAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'meetup', 'sort_order', 'talk_duration_min')
    list_filter  = ('meetup',)
    inlines      = [TalkTranslationInline]
