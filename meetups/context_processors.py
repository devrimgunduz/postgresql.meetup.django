from .models import Language


def site_context(request):
    lang      = getattr(request, 'current_lang', 'en')
    languages = Language.get_active()
    return {
        'current_lang': lang,
        'active_languages': languages,
        'is_tr': lang == 'tr',
    }
