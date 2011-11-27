$(document).ready(function() {
  
  // Clear text in field when clicked.
  $('.new_task input').focus(function() {
    $(this).val('');
  });

  $('.submit_new_task').click(function() {
    newTask($(this).siblings('input'));
  });

  // On enter keypress.
  $('.new_task input').keydown(function(e) {
    if (e.which == 13 ) {
       newTask($(this));
       return false;
     }
  });
  
  
  $('.task').live('mouseenter mouseleave', function(event) {
    if ( event.type == "mouseenter" ) {
      $(this).find('.delete_task').show();
    } else {
      $(this).find('.delete_task').hide();
      $(this).find('.confirm_delete_task').hide();
    }
  });
  
  $('.task').live('click', (function() {
    $(this).find('.delete_task').show();
    // if (!$(this).hasClass('archived')) {
    //   $(this).addClass('archived');
    // }
    // else {
    //   $(this).removeClass('archived');
    // }
  }));

  $('.delete_task').live('click', function() {
    $(this).siblings('.confirm_delete_task').show();
  });

  $('.confirm_delete_task').live('click', function() {
    // Argument is the task
    deleteTask($(this).parents('.task'));
  });

});

// Receives the input box with the new task name.
function newTask(new_task_input) {
  var bad_entry = false;
  new_task_name = new_task_input.val();
  new_task_input
    .parents('.category')
    .find('.task_name')
    .each(function() {
      // If duplicate.
      if ((new_task_name == $(this).text()) || new_task_name == '') {
        bad_entry = true;
    }
  })
  if (bad_entry) {
    showFailure(new_task_input);
  }
  else {
    var data = {
      name: new_task_input.val(),
      id: parseInt(new_task_input
                     .parents('.category')
                     .find('.task')
                     .length) + 1,
      category_name: new_task_input
                       .parents('.category')
                       .find('.category_name')
                       .text()
                       .toLowerCase(),
      category_id: new_task_input
                     .parents('.category')
                     .attr('id')
                     .split('-')[1]
    };
    $.get('http://mkromgmt.appspot.com/ajax?action=new_task&' + $.param(data), function(data) {
      data = $.parseJSON(data);
      new_task_input.val('+ new');
      new_task_input
        .parents('.category')
        .find('.tasks')
        .append('\
          <p class="task" id="task-' + data['category_id'] + '-' + data['id'] + '">\
          <span class="task_name">' + data['name'] + '\
          </span><span class="delete_task_links">\
          <a class="delete_task">&nbsp;&times;</a>&nbsp;\
          <a class="confirm_delete_task">really?</a></p>');
        showSuccess(new_task_input
                      .parents('.category')
                      .find('.task:last-child'));
    });
  }
}

function deleteTask(task_to_delete) {
  var data = {
    id: parseInt(task_to_delete
                   .attr('id')
                   .split('-')[2]),
    category_id: task_to_delete
                   .parents('.category')
                   .attr('id')
                   .split('-')[1]
  };
  $.get('http://mkromgmt.appspot.com/ajax?action=delete_task&' + $.param(data), function(data) {
    showFailure(task_to_delete);
    $(task_to_delete).remove();
  })
}

function showSuccess(status_indicator) {
  $(status_indicator).css('background-color', '#33CC00');
  $(status_indicator).css('color', '#FFFFFF');
  setTimeout(
    function() {
      $(status_indicator).css('background-color', '#FFFFFF');
      $(status_indicator).css('color', '#999999');
    },
    250
  )
}

function showFailure(status_indicator) {
  $(status_indicator).css('background-color', '#FF0000');
  setTimeout(
    function() {
      $(status_indicator).css('background-color', '#FFFFFF')
    },
    250
  )  
}