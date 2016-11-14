from arche_celery.utils import build_status
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid_celery import celery_app


def task_status(request, task_id=None):
    """
    :param request: Pyramid request object
    :return: dict with status info
    """
    #Check that this is an instance of...?
    if task_id is None:
        task_id = request.matchdict['task_id']
    async_res = celery_app.AsyncResult(task_id)
    return build_status(async_res)


def includeme(config):
    config.add_route(
        'task_status',
        '/_task_status/{task_id}')
    config.add_view(
        task_status,
        route_name='task_status',
        permission=NO_PERMISSION_REQUIRED,
        renderer='json',
    )
