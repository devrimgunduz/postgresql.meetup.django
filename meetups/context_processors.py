from django.db import OperationalError, ProgrammingError


def site_context(request):
    lang = getattr(request, 'current_lang', 'en')
    try:
        from .models import Language
        languages = Language.get_active()
    except (OperationalError, ProgrammingError):
        languages = []
    return {
        'current_lang':     lang,
        'active_languages': languages,
        'is_tr':            lang == 'tr',
    }
