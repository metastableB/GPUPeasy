
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
