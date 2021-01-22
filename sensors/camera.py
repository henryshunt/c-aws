if config.sensors["camera"]["enabled"] == True:
    try:
        with picamera.PiCamera() as camera:
            pass
    except Exception as e:
        helpers.log(None, "sampler", "Failed to open connection to camera")
        raise SensorError("Failed to open connection to camera", e)
                
def camera_report(self, time):
    utc_minute = str(utc.minute)
    if not utc_minute.endswith("0") and not utc_minute.endswith("5"):
        return

    # Only take images between sunrise and sunset
    sun_times = helpers.solar_times(helpers.utc_to_local(utc))    
    sunset_threshold = sun_times[0] + timedelta(minutes=60)
    sunrise_threshold = sun_times[0] - timedelta(minutes=60)
    if utc < sunrise_threshold or utc > sunset_threshold: return

    # Check the filesystem
    try:
        if (not os.path.isdir(config.camera_directory) or 
            not os.path.ismount(config.camera_directory)):
            helpers.data_error("operation_log_camera() 0")
            return

    except:
        helpers.data_error("operation_log_camera() 1")
        return

    free_space = helpers.remaining_space(config.camera_directory)
    if free_space == None or free_space < 0.1:
        helpers.data_error("operation_log_camera() 2")
        return


    try:
        image_dir = os.path.join(config.camera_directory, 
            utc.strftime("%Y/%m/%d"))
        if not os.path.isdir(image_dir): os.makedirs(image_dir)
        image_name = utc.strftime("%Y-%m-%dT%H-%M-%S")
    
        # Set image resolution, wait for auto settings, then capture
        with picamera.PiCamera() as camera:
            camera.resolution = (1280, 960)
            time.sleep(2.5)
            camera.capture(os.path.join(image_dir, image_name + ".jpg"))

        # Write data to upload database
        if config.camera_uploading == True:
            values = (utc.strftime("%Y-%m-%d %H:%M:%S"),)
            query = data.query_database(config.upload_db_path,
                "INSERT INTO camReports VALUES (?)", values)

            if query == False:
                helpers.data_error("operation_log_camera() 4")
    except: helpers.data_error("operation_log_camera() 3")