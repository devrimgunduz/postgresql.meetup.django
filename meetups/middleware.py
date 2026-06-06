from .models import Language


class LanguageMiddleware:
    """
    Reads ?lang= from query string, validates it against active languages,
    and stores the result on request.current_lang for use in views/templates.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        active_codes = list(
            Language.objects.filter(is_active=True).values_list('code', flat=True)
        )
        requested = request.GET.get('lang', request.session.get('lang', ''))
        if requested in active_codes:
            request.current_lang = requested
            request.session['lang'] = requested
        else:
            default = Language.get_default()
            request.current_lang = default.code if default else 'en'

        return self.get_response(request)
