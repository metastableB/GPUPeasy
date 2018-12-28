
function ajaxGetJobStatus(){
  $("#ScheduledJobs").load("scheduledjobs");
  $("#SuccessfulJobs").load("successfuljobs");
  $("#FailedJobs").load("failedjobs");
  $("#DeviceUtilization").load("deviceutilization");
}

function initialization(){
  ajaxGetJobStatus();
}

$(document).ready(function() {
  // show animation for 1/2 a second
  setTimeout(initialization, 500);
  // Update every 10 seconds
  setInterval(ajaxGetJobStatus, 10000);
});

function loadLogLines(formId, textAreaId) {
  // Assume that element has a form
  var gt = document.getElementById(formId);
  var fileName = gt.elements['fileName']['value'];
  var N = gt.elements['lastN']['value'];
  // Post the form data and get the jquery response
  var formData = $('#' + formId).serializeArray();
  var resp = $.post(
    '/loadlogfile', // URL
    formData, // Data
    function(response) { // Call-back
      textAreaId = '#' + textAreaId
      console.log(response);
      $(textAreaId).text(response['value']);
    }, 'json' // Response type
  );
}
