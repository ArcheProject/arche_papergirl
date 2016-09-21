
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
    $('[data-send-list]').on('click', send_to_list);
    $('[data-replace-target]').on('click', load_and_replace);
});


function send_to_list(event) {
    arche.actionmarker_feedback($(event.currentTarget), true);
    event.preventDefault();
    var url = $(event.currentTarget).attr('href');
    var request = arche.do_request(url);
    request.done(function(response) {
        update_progress(response['pending']);
        if (response['pending'] > 0) {
            $('[data-send-list]').click();
        } else {
            arche.actionmarker_feedback($(event.currentTarget), false);
        }
    });
    request.fail(function(jqXHR) {
        arche.flash_error(jqXHR);
        arche.actionmarker_feedback($(event.currentTarget), false);
    });
}


function update_progress(curr_pending) {
    var orig_elem = $('[data-pending]');
    var orig_value = parseInt(orig_elem.data('orig-value'));
    var progress_elem = $('[data-progress]');
    progress_elem.css({'width': Math.floor(((orig_value-curr_pending) / orig_value) * 100) + '%'});
    orig_elem.html(curr_pending);
    $('[data-completed]').html(orig_value-curr_pending);
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