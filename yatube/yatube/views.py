from http import HTTPStatus

from django.shortcuts import render


def page_not_found(request, exception=None):
    return render(request, "misc/404.html",
                  {"path": request.path},
                  status=HTTPStatus.NOT_FOUND)


def server_error(request):
    return render(request, "misc/500.html",
                  status=HTTPStatus.INTERNAL_SERVER_ERROR)
