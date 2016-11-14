
var subscribers_table_tpl;


function subscribers_table_from_response(response) {
    if (typeof(subscribers_table_tpl) === 'undefined') {
        subscribers_table_tpl = $("#list-subscribers").clone().html();
    } else {
        $("#list-subscribers").html(subscribers_table_tpl);
    }

    var directive = {'tr':
        {'obj<-items':
            {
                '.email': 'obj.email',
                '.created': 'obj.created',
                '.modified': 'obj.modified',
                '.list_tags': 'obj.list_tags',
                '.edit_subs@href+': function(args) {
                    return '/' + args.item['name'] + '/edit'
                }
            }
        }
    };
    $("#list-subscribers [data-load-msg]").remove();
    $('#list-subscribers').render(response, directive);
}


$(function () {
    $('[data-send-list-celery]').on('click', send_to_list_celery);
    $('[data-replace-target]').on('click', load_and_replace);
});


function send_to_list_celery(event) {
    arche.actionmarker_feedback($(event.currentTarget), true);
    $(event.currentTarget).addClass('disabled');
    event.preventDefault();
    var url = $(event.currentTarget).attr('href');
    var request = arche.do_request(url);
    request.done(function(response) {
        $('[data-celery-terminate]').removeClass('disabled');
        update_result_celery(response['status_url'], $(event.currentTarget));
    });
    request.fail(function(jqXHR) {
        arche.flash_error(jqXHR);
        arche.actionmarker_feedback($(event.currentTarget), false);
        $(event.currentTarget).removeClass('disabled');
    });
}


function update_result_celery(url, actionmarker) {
    var request = arche.do_request(url);
    var url = url;
    var actionmarker = actionmarker;
    request.done(function(response) {
        update_progress(response['children']['total']-response['children']['completed'], response['children']['total']);
        if (response['all_ready'] == true) {
            arche.actionmarker_feedback(actionmarker, false);
            $('[data-celery-terminate]').addClass('disabled');
            update_status();
        } else {
            setTimeout(function() {
                update_result_celery(url, actionmarker);
            }, 1000);
        }
    });
}


function update_progress(curr_pending, orig_value) {
    var orig_elem = $('[data-pending]');
    var progress_elem = $('[data-progress]');
    progress_elem.css({'width': Math.floor(((orig_value-curr_pending) / orig_value) * 100) + '%'});
    orig_elem.html(curr_pending);
    $('[data-completed]').html(orig_value-curr_pending);
}


function read_task_celery(task_id, other_deferred) {
    var url = "/_task_status/" + task_id;
    var task_id = task_id;
    var other_deferred = other_deferred;
    var request = arche.do_request(url);
    request.done(function(response) {
        if (response['ready'] == true) {
            other_deferred.resolve(response);
        } else {
            setTimeout(function() {
                read_task_celery(task_id, other_deferred);
            }, 1000);
        }
    });
}


function wait_for_task(task_id) {
    var dfd = new $.Deferred();
    read_task_celery(task_id, dfd);
    return dfd.promise();
}


function update_status() {
    var url = './status.json';
    var request = arche.do_request(url);
    request.done(function(response) {
        $('[data-nl-status="queue"]').html(response['queue']);
        $('[data-nl-status="delivered"]').html(response['delivered']);
        $('[data-nl-status="error"]').html(response['error']);
        if ((response['queue'] > 0) && (response['running_task_id']) == null) {
            $('[data-send-list-celery]').removeClass('disabled');
            $('[data-send-area]').removeClass('hidden');
        }
    });
}


function load_and_replace(event) {
    event.preventDefault();
    var elem = $(event.currentTarget);
    arche.actionmarker_feedback(elem, true);
    var url = elem.attr('href');
    var request = arche.do_request(url);
    var target = $(elem.data('replace-target'));
    if (target.length != 1) {
        target = elem;
    }
    request.done(function(response) {
        target.html(response);
    });
    request.fail(arche.flash_error);
    request.always(function() {
        arche.actionmarker_feedback(elem, false);
        arche.load_flash_messages();
    });
}
