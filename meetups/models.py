from django.db import models
from django.utils import timezone


class Language(models.Model):
    code       = models.CharField(max_length=10, unique=True)   # 'en', 'tr', 'de'
    label      = models.CharField(max_length=64)                # 'English', 'Türkçe'
    is_default = models.BooleanField(default=False)
    is_active  = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order', 'id']

    def __str__(self):
        return f'{self.label} ({self.code})'

    def save(self, *args, **kwargs):
        # Enforce single default
        if self.is_default:
            Language.objects.exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    @classmethod
    def get_default(cls):
        return cls.objects.filter(is_default=True).first() \
            or cls.objects.filter(is_active=True).first()

    @classmethod
    def get_active(cls):
        return cls.objects.filter(is_active=True).order_by('sort_order', 'id')


class Meetup(models.Model):
    STATUS_CHOICES = [
        ('draft',     'Draft'),
        ('published', 'Published'),
        ('past',      'Past'),
    ]
    status           = models.CharField(max_length=16, choices=STATUS_CHOICES, default='draft')
    event_date       = models.DateTimeField(null=True, blank=True)
    event_end        = models.DateTimeField(null=True, blank=True)
    venue_address    = models.TextField(blank=True)
    venue_map_url    = models.URLField(blank=True)
    registration_url = models.URLField(blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        name = self.get_translation('venue_name') or f'Meetup #{self.pk}'
        date = self.event_date.strftime('%Y-%m-%d') if self.event_date else 'no date'
        return f'{name} ({date})'

    def get_translation(self, field='meetup_title', lang_code=None):
        """Get a translated field value, falling back to default language."""
        if lang_code:
            val = self.translations.filter(lang=lang_code, field=field).first()
            if val and val.value:
                return val.value
        # Fallback to default language
        default = Language.get_default()
        if default:
            val = self.translations.filter(lang=default.code, field=field).first()
            if val:
                return val.value
        return ''

    def translations_dict(self):
        """Return {lang: {field: value}} dict for template use."""
        out = {}
        for t in self.translations.all():
            out.setdefault(t.lang, {})[t.field] = t.value
        return out

    @classmethod
    def auto_archive(cls):
        from django.db import OperationalError, ProgrammingError
        try:
            cutoff = timezone.now() - timezone.timedelta(hours=6)
            cls.objects.filter(status='published', event_date__lt=cutoff).update(status='past')
        except (OperationalError, ProgrammingError):
            pass

    @classmethod
    def get_next(cls):
        cls.auto_archive()
        return cls.objects.filter(status='published').order_by('event_date').first()

    @classmethod
    def get_past(cls):
        cls.auto_archive()
        return cls.objects.filter(status='past').order_by('-event_date')


class MeetupTranslation(models.Model):
    FIELD_CHOICES = [
        ('meetup_title', 'Meetup Title'),
        ('notes',      'Notes'),
    ]
    meetup = models.ForeignKey(Meetup, on_delete=models.CASCADE, related_name='translations')
    lang   = models.CharField(max_length=10)
    field  = models.CharField(max_length=64, choices=FIELD_CHOICES)
    value  = models.TextField(blank=True)

    class Meta:
        unique_together = ('meetup', 'lang', 'field')

    def __str__(self):
        return f'{self.meetup_id} [{self.lang}] {self.field}'


class Talk(models.Model):
    meetup            = models.ForeignKey(Meetup, on_delete=models.CASCADE, related_name='talks')
    sort_order        = models.IntegerField(default=0)
    speaker_name      = models.CharField(max_length=255, blank=True)
    speaker_photo_url = models.URLField(blank=True)
    talk_duration_min = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        title = self.get_translation('talk_title') or 'Untitled'
        return f'{title} – {self.speaker_name}'

    def get_translation(self, field='meetup_title', lang_code=None):
        if lang_code:
            val = self.translations.filter(lang=lang_code, field=field).first()
            if val and val.value:
                return val.value
        default = Language.get_default()
        if default:
            val = self.translations.filter(lang=default.code, field=field).first()
            if val:
                return val.value
        return ''

    def translations_dict(self):
        out = {}
        for t in self.translations.all():
            out.setdefault(t.lang, {})[t.field] = t.value
        return out


class TalkTranslation(models.Model):
    FIELD_CHOICES = [
        ('talk_title',    'Talk Title'),
        ('talk_abstract', 'Abstract'),
        ('speaker_bio',   'Speaker Bio'),
    ]
    talk  = models.ForeignKey(Talk, on_delete=models.CASCADE, related_name='translations')
    lang  = models.CharField(max_length=10)
    field = models.CharField(max_length=64, choices=FIELD_CHOICES)
    value = models.TextField(blank=True)

    class Meta:
        unique_together = ('talk', 'lang', 'field')

    def __str__(self):
        return f'{self.talk_id} [{self.lang}] {self.field}'
