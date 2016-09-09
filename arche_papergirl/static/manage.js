
$(function () {
    $('[data-send-list]').on('click', function(event) {
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
    });

    $('[data-replace-target]').on('click', load_and_replace);
});


function update_progress(curr_pending) {
    var orig_elem = $('[data-pending]');
    var orig_value = parseInt(orig_elem.data('to-process'));
    var progress_elem = $('[data-progress]');
    progress_elem.css({'width': Math.floor(((orig_value - curr_pending) / orig_value) * 100) + '%'});
    orig_elem.data('to-process', curr_pending);
}

function load_and_replace(event) {
  event.preventDefault();
  var elem = $(event.currentTarget);
  arche.actionmarker_feedback(elem, true);
  var url = elem.attr('href');
  var request = arche.do_request(url);
  var target = $(elem.data('replace-target'))
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