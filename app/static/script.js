function convertSecondsToMinutesSeconds(totalSeconds) {
  const minutes = Math.floor(totalSeconds / 60); // Get the whole number of minutes
  const seconds = totalSeconds % 60; // Get the remaining seconds using the modulo operator

  const formattedSeconds = seconds < 10 ? '0' + seconds : seconds;

  return `${minutes}:${formattedSeconds}`;
}

console.log("Integer from Flask:", timeleft);
var downloadTimer = setInterval(function(){
  if(timeleft <= 0){
    clearInterval(downloadTimer);
    document.getElementById("countdown").innerHTML = "0:00";
  } else {
    document.getElementById("countdown").innerHTML = convertSecondsToMinutesSeconds(timeleft);
  }
  timeleft -= 1;
}, 1000);

function updateChildChoices() {
            var actionCategory = $('#action').val();
            if (!actionCategory) {
                return; 
            }
            $.getJSON('/get_action_choices/' + actionCategory, function(data) {
                var targetSelect = $('#target');
                targetSelect.empty();
                $.each(data, function(index, item) {
                    targetSelect.append($('<option>', {
                        value: item[0],
                        text: item[1]
                    }));
                });
            });
        }
        // Call on page load to initialize if a default parent is selected
        $(document).ready(function() {
            updateChildChoices();
        });