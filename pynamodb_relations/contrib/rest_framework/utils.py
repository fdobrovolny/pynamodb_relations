from django.http import Http404
from pynamodb.exceptions import DoesNotExist


def get_object_or_404(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except DoesNotExist:
        raise Http404('No %s matches the given query.' % func.__self__.__name__)
