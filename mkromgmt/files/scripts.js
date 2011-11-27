var autosave_scheduled = false;
var schedule_autosave_timer;
var finished_typing_timer;

$(document).ready(function() {
  setHoverEvents();
  setClickEvents();
  fetchCompleteTasks();
  
  $('#journal').keydown(function() {
    // cancel timeout that saves when user has finished typing
    clearTimeout(finished_typing_timer);
    finished_typing_timer = setTimeout(function() {autosave(date)}, 1000);
    
    // date of the entry
    var date = getDate($('.date_label.selected').html());
    
    // schedule the next autosave
    // this happens every 20 seconds using the global var autosave_scheduled
    // it's reset to false when the entry is successfully saved so that when the
    // next key is pressed, another autosave is scheduled 20 seconds later 
    if (autosave_scheduled == false) {
      autosave_scheduled = true;
      schedule_autosave_timer = setTimeout(function() {autosave(date)}, 15000);
    }
    
    // save the entry 2 seconds after the user finished typing
    // this is cancelled when the user starts typing again
  })
  
  if ($('#journal textarea').length > 0) {  
    var journal_offset = $('#journal textarea').offset();
    journal_height = $(window).height() - journal_offset.top - 50;
    $('#journal textarea').width($(window).width() / 2);
    $('#journal textarea').height(journal_height);
  }
})

function autosave(date) {

  <input id="first_name" />
  var data = {
    first_name: $('#journal textarea').val(),
    last_name: $('#first_name').val();
  }
  var data = {
    text: $('#journal textarea').val(),
    timestamp: date
  }
  $.get('http://mkromgmt.appspot.com/ajax?action=save_journal_entry&' + $.param(data), function(data) {
    if (data == 'success') { 
      // reset scheduled autosave so another one can be scheduled
      clearTimeout(schedule_autosave_timer);
      autosave_scheduled = false;
      showSuccess('#status_indicator');
    }
  })
}

function setClickEvents() {
    $('.task').click(function() {
    if ($(this).hasClass('complete')) {
      $(this).removeClass('complete');
      incompleteTask($(this).attr('id'));
    }
    else {
      $(this).addClass('complete');
      completeTask($(this).attr('id'));
    }
  })
  
  $('.date_label').click(
    function() {
      $('.date_label').removeClass('selected');
      $('#journal textarea').val('');
      $(this).addClass('selected');
      var data = {timestamp: getDate($(this).html())};
      $.get('http://mkromgmt.appspot.com/ajax?action=fetch_journal_entry&' + $.param(data), function(data) {
        $('#journal textarea').val(data);
        $('#journal textarea').focus();
      })
    }
  )
}

function setHoverEvents() {
  $('.task').hover(
    function() {
      i = $(this).attr('id').split('-');
      $(this).css('background-color', '#EEEEEE');
      $('#date-' + i[0]).find('.date_label').css('background-color', '#EEEEEE');
      $('#category-' + i[1]).css('background-color', '#EEEEEE');
      $('#task-' + i[1] + '-' + i[2]).css('background-color', '#EEEEEE');
    },
    function() {
      i = $(this).attr('id').split('-');
      $(this).css('background-color', '#FFFFFF');
      $('#date-' + i[0]).find('.date_label').css('background-color', '#FFFFFF');
      $('#category-' + i[1]).css('background-color', '#FFFFFF');
      $('#task-' + i[1] + '-' + i[2]).css('background-color', '#FFFFFF');
    }
  );
  
  $('.date_label').hover(
    function() {
      $(this).css('background-color', '#EEEEEE');
    },
    function() {
      $(this).css('background-color', '#FFFFFF');
    }
  );
}

function completeTask(task) {
  var task = task.split('-');
  var date = getDate($('#date-' + task[0]).find('.date_label').html());
  var name = $('#task-' + task[1] + '-' + task[2]).html();
  var id = task[2]
  var category_name = $('#category-' + task[1]).html();
  var category_id = task[1];
  var data = {
    date: date,
    category_name: category_name,
    category_id: category_id,
    name: name,
    id: id
  }
  $.get('http://mkromgmt.appspot.com/ajax?action=complete_task&' + $.param(data), function(data) {
    if (data == 'success') {showSuccess('#status_indicator');}
  })
}

function incompleteTask(task) {
  var task = task.split('-');
  var date = getDate($('#date-' + task[0]).find('.date_label').html());
  var name = $('#task-' + task[1] + '-' + task[2]).html();
  var id = task[2];
  var category_name = $('#category-' + task[1]).html();
  var category_id = task[1];
  var data = {
    date: date,
    category_name: category_name,
    category_id: category_id,
    name: name,
    id: id
  }
  $.get('http://mkromgmt.appspot.com/ajax?action=incomplete_task&' + $.param(data), function(data) {
    if (data == 'success') {showSuccess('#status_indicator');}
  })
}

function autosaveJournalEntry() {
  var user_is_typing = setTimeout('autosave()', 20000)
}

function getDate(date) {
  // converts the displayed date to a timestamp
  date = date.split(' ');
  var year = new Date();
  var timestamp = new Date(year.getFullYear(), getMonth(date[1]), date[2]);
  timestamp = timestamp.getTime()/1000 - (timestamp.getTimezoneOffset() * 60);
  return timestamp;
}

function getMonth(month_name) {
  switch(month_name)
  {
    case 'JAN':
      return 0;
      break;
    case 'FEB':
      return 1;
      break;
    case 'MAR':
      return 2;
      break;
    case 'APR':
      return 3;
      break;
    case 'MAY':
      return 4;
      break;
    case 'JUN':
      return 5;
      break;
    case 'JUL':
      return 6;
      break;
    case 'AUG':
      return 7;
      break;
    case 'SEP':
      return 8;
      break;
    case 'OCT':
      return 9;
      break;
    case 'NOV':
      return 10;
      break;
    case 'DEC':
      return 11;
      break;
  }
}

function showSuccess(status_indicator) {
  $(status_indicator).show();
  setTimeout(
    function() {
      $(status_indicator).hide();
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

function fetchCompleteTasks() {
  $.get('http://mkromgmt.appspot.com/ajax?action=fetch_complete_tasks', function(data) {
    data = $.parseJSON(data);
    for (i in data['tasks']) {
      $('#' + data['tasks'][i]).addClass('complete');
    }
  });
}