from django.shortcuts import render
from .models import Meetup, Language


def index(request):
    lang   = request.current_lang
    meetup = Meetup.get_next()
    ctx = {
        'meetup': meetup,
        'lang':   lang,
        'tr':     meetup.translations_dict() if meetup else {},
        'talks':  [],
    }
    if meetup:
        talks = []
        for talk in meetup.talks.prefetch_related('translations'):
            talks.append({
                'obj': talk,
                'tr':  talk.translations_dict(),
            })
        ctx['talks'] = talks
    return render(request, 'meetups/index.html', ctx)


def previous(request):
    lang    = request.current_lang
    meetups = []
    for m in Meetup.get_past().prefetch_related('translations', 'talks__translations'):
        talks = [{'obj': t, 'tr': t.translations_dict()} for t in m.talks.all()]
        meetups.append({'obj': m, 'tr': m.translations_dict(), 'talks': talks})
    return render(request, 'meetups/previous.html', {'meetups': meetups, 'lang': lang})
