
function ajaxGetJobStatus(){
  //$("#ScheduledJobs").load("scheduledjobs");
  //$("#SuccessfulJobs").load("successfuljobs");
  //$("#FailedJobs").load("failedjobs");
  $("#DeviceUtilization").load("deviceutilization");
}

$(document).ready(function() {
  setInterval(ajaxGetJobStatus, 5000);
});
