function displayLocalTime() {
    var timestamp = new Date();
    
    var nowDate = zeroPad(timestamp.getDate());
    var nowMonth = zeroPad(timestamp.getMonth() + 1);
    var nowYear = zeroPad(timestamp.getFullYear());
    var nowHour = zeroPad(timestamp.getHours());
    var nowMinute = zeroPad(timestamp.getMinutes());
    var nowSecond = zeroPad(timestamp.getSeconds());

    var formatted = nowDate + "/" + nowMonth + "/" + nowYear + 
        " at " + nowHour + ":" + nowMinute + ":" + nowSecond;
    document.getElementById("item_local_time").innerHTML = formatted;
}

function zeroPad(value) {
    if (value < 10) {
        value = "0" + value;
    }

    return value;
}