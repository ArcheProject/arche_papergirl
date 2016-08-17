
$(function () {
    $('[data-send-list-for]').on('click', function(event) {
        arche.actionmarker_feedback($(event.currentTarget), true);
        event.preventDefault();
        var url = $(event.currentTarget).attr('href');
        var request = arche.do_request(url);
        request.done(function(response) {
            update_progress(response['list_uid'], response['pending']);
            if (response['pending'] > 0) {
                $('[data-send-list-for="' + response['list_uid'] + '"]').click();
            } else {
                arche.actionmarker_feedback($(event.currentTarget), false);
            }
        });
        request.fail(function(jqXHR) {
            arche.flash_error(jqXHR);
            arche.actionmarker_feedback($(event.currentTarget), false);
        });
    });
});


function update_progress(uid, curr_pending) {
    var orig_elem = $('[data-pending-for="' + uid + '"]');
    var orig_value = parseInt(orig_elem.data('to-process'));
    var progress_elem = $('[data-progress-for="' + uid + '"]');
    progress_elem.css({'width': Math.floor(((orig_value - curr_pending) / orig_value) * 100) + '%'});
    orig_elem.data('to-process', curr_pending);
}
