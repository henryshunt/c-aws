function displayLocalTime() {
    var local_time = new Date();

    var nowDate = zeroPad(local_time.getDate());
    var nowMonth = zeroPad(local_time.getMonth() + 1);
    var nowYear = zeroPad(local_time.getFullYear());
    var nowHour = zeroPad(local_time.getHours());
    var nowMinute = zeroPad(local_time.getMinutes());
    var nowSecond = zeroPad(local_time.getSeconds());

    var formatted = nowDate + "/" + nowMonth + "/" + nowYear + 
        " at " + nowHour + ":" + nowMinute + ":" + nowSecond;
    document.getElementById("item_local_time").innerHTML
        = formatted;
}

function zeroPad(value) {
    if (value < 10) {
        value = "0" + value;
    }

    return value;
}

function queryParam(key) {
    key = key.replace(/[*+?^$.\[\]{}()|\\\/]/g, "\\$&");
    var match = location.search.match(new RegExp("[?&]" + key + "=([^&]+)(&|$)"));
    return match && decodeURIComponent(match[1].replace(/\+/g, " "));
}