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
    document.getElementById("item_local_time").innerHTML = formatted;
}

function zeroPad(value) {
    if (value < 10) { value = "0" + value; }
    return value.toString();
}

function queryParam(key) {
    key = key.replace(/[*+?^$.\[\]{}()|\\\/]/g, "\\$&");
    var match = location.search.match(new RegExp("[?&]" + key + "=([^&]+)(&|$)"));
    return match && decodeURIComponent(match[1].replace(/\+/g, " "));
}

function displayValue(value, id, units, precision) {
    if (value != null) {
        if (precision == null) {
            document.getElementById(id).innerHTML = value + units;

        } else {
            document.getElementById(id).innerHTML = value.toFixed(precision) + units;
        }
    } else { document.getElementById(id).innerHTML = "no data"; }
}

function degreesToCompass(degrees) {
    if (degrees >= 338 || degrees < 23) { return "N"; }
    else if (degrees >= 23 && degrees < 68) { return "NE"; }
    else if (degrees >= 68 && degrees < 113) { return "E"; }
    else if (degrees >= 113 && degrees < 158) { return "SE"; }
    else if (degrees >= 158 && degrees < 203) { return "S"; }
    else if (degrees >= 203 && degrees < 248) { return "SW"; }
    else if (degrees >= 248 && degrees < 293) { return "W"; }
    else if (degrees >= 293 && degrees < 338) { return "NW"; }
}