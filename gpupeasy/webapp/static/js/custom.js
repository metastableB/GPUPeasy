
function ajaxGetJobStatus(){
  $("#ScheduledJobs").load("scheduledjobs");
  $("#SuccessfulJobs").load("successfuljobs");
  $("#FailedJobs").load("failedjobs");
  $("#DeviceUtilization").load("deviceutilization");
}

$(document).ready(function() {
  ajaxGetJobStatus();
  setInterval(ajaxGetJobStatus, 5000);
  $('.hide-5').show().delay(5000).fadeOut();
});
