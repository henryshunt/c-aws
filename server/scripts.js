function display_local_time() {
    var timestamp = new Date();
    
    var now_date = zero_pad(timestamp.getDate());
    var now_month = zero_pad(timestamp.getMonth() + 1);
    var now_year = zero_pad(timestamp.getFullYear());
    var now_hour = zero_pad(timestamp.getHours());
    var now_minute = zero_pad(timestamp.getMinutes());
    var now_second = zero_pad(timestamp.getSeconds());

    var formatted = now_date + "/" + now_month + "/" + now_year + 
        " at " + now_hour + ":" + now_minute + ":" + now_second;
    document.getElementById("local_time").innerHTML = formatted;
}

function zero_pad(value) {
    if (value < 10) {
        value = "0" + value;
    }

    return value;
}