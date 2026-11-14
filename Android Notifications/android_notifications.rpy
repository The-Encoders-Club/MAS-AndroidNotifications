# -*- coding: utf-8 -*-
# Android Notifications submod
# Monika sends notifications on Android when the player leaves with a farewell,
# on holidays, and when the player opens some apps (while MAS is in PiP or a floating window)
#
# Settings are saved in config.json, next to this file
# Messages are in android_notifications_messages.rpy

#The name, version and updater of the submod are in header.rpy

init -5 python in android_notifs:
    import io
    import json
    import os
    import datetime
    import store
    from store import mas_utils

    #START: Paths
    def _findSubmodDir():
        """
        Finds this submod's folder, so it still works if the player renames it

        OUT:
            folder relative to the Monika After Story folder (e.g. "game/Submods/Android Notifications")
        """
        for filename in renpy.list_files():
            filename = filename.replace("\\", "/")
            if filename.endswith("/android_notifications.rpy") or filename.endswith("/android_notifications.rpyc"):
                return "game/" + os.path.dirname(filename)

        return "game/Submods/Android Notifications"

    SUBMOD_DIR = _findSubmodDir()
    CONFIG_PATH = os.path.join(renpy.config.basedir, SUBMOD_DIR, "config.json")

    def getImage(name):
        """
        Gets the image_path of one of this submod's avatars

        IN:
            name - avatar name (e.g. "monika_wink")

        OUT:
            image_path, relative to the Monika After Story folder
        """
        return "{0}/notif/{1}.png".format(SUBMOD_DIR, name)

    #START: Config
    CONFIG_VERSION = 1

    #Setting -> default value
    DEFAULT_CONFIG = {
        "school_minutes": 420,
        "work_minutes": 480,
        "shopping_minutes": 30,
        "eat_minutes": 25,
        "wake_up_minutes": 360,
        "interactive_minutes": 180,
        "followup_seconds": 30,
        "followups_enabled": True,
        "holidays_enabled": True,
        #Testing only (not shown in the settings): times count in seconds instead of minutes
        "test_mode": False,
    }

    #Setting -> values the player can pick
    CONFIG_OPTIONS = {
        "school_minutes": [180, 240, 300, 360, 420, 480],
        "work_minutes": [240, 300, 360, 420, 480, 540, 600],
        "shopping_minutes": [15, 30, 45, 60, 90, 120],
        "eat_minutes": [15, 20, 25, 30, 45, 60],
        "wake_up_minutes": [300, 330, 360, 390, 420, 450, 480, 510, 540, 570, 600],
        "interactive_minutes": [15, 30, 60, 120, 180],
        "followup_seconds": [15, 30, 60, 120, 180],
    }

    config = dict(DEFAULT_CONFIG)

    def loadConfig():
        """
        Loads config.json. Missing or invalid values use the defaults
        """
        global config
        config = dict(DEFAULT_CONFIG)

        if not os.path.isfile(CONFIG_PATH):
            saveConfig()
            return

        try:
            with io.open(CONFIG_PATH, "r", encoding="utf-8") as config_file:
                data = json.load(config_file)

        except Exception as e:
            mas_utils.mas_log.error("[Android Notifications] Failed to read config.json, using defaults: {}".format(e))
            return

        #NOTE: no isinstance(data, dict), in Ren'Py dict is RevertableDict and json returns a plain dict
        if not hasattr(data, "get"):
            return

        for key, default in DEFAULT_CONFIG.items():
            value = data.get(key)
            if isinstance(default, bool):
                if isinstance(value, bool):
                    config[key] = value

            elif value in CONFIG_OPTIONS.get(key, ()):
                config[key] = value

    def saveConfig():
        """
        Saves config.json. It's written to a temp file first, so a crash
        while saving can't leave a broken file
        """
        data = dict(config)
        data["version"] = CONFIG_VERSION
        temp_path = CONFIG_PATH + ".tmp"

        try:
            with io.open(temp_path, "w", encoding="utf-8") as config_file:
                config_file.write(unicode(json.dumps(data, indent=4, sort_keys=True)))

            #os.rename can't replace files on Windows
            if os.name == "nt" and os.path.exists(CONFIG_PATH):
                os.remove(CONFIG_PATH)
            os.rename(temp_path, CONFIG_PATH)

        except Exception as e:
            mas_utils.mas_log.error("[Android Notifications] Failed to save config.json: {}".format(e))

    def toggleSetting(key):
        """
        Toggles a boolean setting, saves it and applies it

        IN:
            key - setting to toggle
        """
        config[key] = not config[key]
        saveConfig()
        registerNotifs()
        renpy.restart_interaction()

    def cycleSetting(key, step):
        """
        Moves a setting to the previous or next value the player can pick, saves it and applies it

        IN:
            key - setting to change
            step - -1 for the previous value, 1 for the next one
        """
        options = CONFIG_OPTIONS[key]
        index = options.index(config[key]) if config[key] in options else 0
        config[key] = options[max(0, min(len(options) - 1, index + step))]
        saveConfig()
        registerNotifs()
        renpy.restart_interaction()

    def formatSetting(key):
        """
        Formats a setting value for the settings screen

        IN:
            key - setting to format

        OUT:
            the formatted value
        """
        value = config[key]
        if key == "wake_up_minutes":
            return "{0}:{1:02d}".format(value // 60, value % 60)

        elif key == "followup_seconds":
            return "{0} s".format(value)

        elif value >= 60:
            if value % 60:
                return "{0} h {1} min".format(value // 60, value % 60)
            return "{0} h".format(value // 60)

        return "{0} min".format(value)

    #Settings shown as time pickers: (setting, label)
    TIME_SETTINGS = [
        ("school_minutes", _("Going to class")),
        ("work_minutes", _("Going to work")),
        ("shopping_minutes", _("Going shopping")),
        ("eat_minutes", _("Going to eat")),
        ("wake_up_minutes", _("Wake up time")),
        ("interactive_minutes", _("Other farewells")),
    ]

    #START: Message helpers
    def _isValentines():
        """
        Checks if today is Valentine's Day
        """
        today = datetime.date.today()
        return today.month == 2 and today.day == 14

    def _farewellMessages(category, valentines=True):
        """
        Gets the messages function for a farewell

        IN:
            category - messages category
            valentines - whether Valentine's Day messages are used on Feb 14
                (Default: True)

        OUT:
            function returning the messages (used by the notification framework)
        """
        def _messages():
            if valentines and _isValentines():
                return MESSAGES["calendar_event"]
            return MESSAGES[category]

        return _messages

    def _foodMessages():
        """
        Picks breakfast, lunch or dinner messages depending on the time

        OUT:
            the messages
        """
        if _isValentines():
            return MESSAGES["calendar_event"]

        hour = datetime.datetime.now().hour
        if 5 <= hour < 12:
            return MESSAGES["morning_food"]

        elif 12 <= hour < 18:
            return MESSAGES["noon_food"]

        return MESSAGES["evening_food"]

    def _delaySeconds(key):
        """
        Converts a time setting (in minutes) to seconds

        IN:
            key - time setting

        OUT:
            seconds (in test mode, the minutes are used as seconds)
        """
        if config["test_mode"]:
            return config[key]
        return config[key] * 60

    def _secondsUntilWakeUp():
        """
        Gets the seconds until the next wake up time

        OUT:
            seconds until the wake up time set by the player (1 minute in test mode)
        """
        if config["test_mode"]:
            return 60

        now = datetime.datetime.now()
        wake_up = datetime.datetime.combine(now.date(), datetime.time(0, 0)) + datetime.timedelta(minutes=config["wake_up_minutes"])
        if wake_up <= now:
            wake_up += datetime.timedelta(days=1)

        return int((wake_up - now).total_seconds())

    def _nextPlayerBday():
        """
        Gets the player's next birthday, after today

        OUT:
            datetime.date, or None if we don't know it
        """
        bday = store.persistent._mas_player_bday
        if not bday:
            return None

        today = datetime.date.today()
        next_bday = mas_utils.add_years(bday, today.year - bday.year)
        if next_bday <= today:
            next_bday = mas_utils.add_years(bday, today.year + 1 - bday.year)

        return next_bday

    def _nextAnniversary():
        """
        Gets the next anniversary milestone (1 week, 1/3/6 months, every year), after today

        OUT:
            datetime.date, or None if there isn't one
        """
        first_session = store.persistent.sessions.get("first_session") if store.persistent.sessions else None
        if not first_session:
            return None

        #first_session is a datetime, but accept a date too
        try:
            first_date = first_session.date()
        except AttributeError:
            first_date = first_session
        today = datetime.date.today()

        milestones = [first_date + datetime.timedelta(days=7)]
        milestones.extend(mas_utils.add_months(first_date, months) for months in (1, 3, 6))
        milestones.extend(
            mas_utils.add_years(first_date, years)
            for years in range(1, today.year - first_date.year + 2)
        )

        future = [milestone for milestone in milestones if milestone > today]
        return min(future) if future else None

    #START: Registration
    #(farewell label, messages category, delay setting, image, alarm)
    NORMAL_FAREWELLS = [
        ("bye_prompt_to_class", "school", "school_minutes", "monika_bored", True),
        ("bye_going_shopping", "shopping", "shopping_minutes", "monika_normal", False),
        ("bye_prompt_to_work", "work", "work_minutes", "monika_wink", True),
    ]

    #(farewell label, messages category, image)
    INTERACTIVE_FAREWELLS = [
        ("bye_prompt_housework", "chores", "monika_angry"),
        ("bye_prompt_workout", "workout", "monika_blushing"),
        ("bye_prompt_game", "play_game", "monika_embarrassed"),
        ("bye_prompt_hangout", "friends", "monika_normal"),
        ("bye_goodbye", "generic_quit", "monika_normal"),
        ("bye_sayanora", "generic_quit", "monika_normal"),
        ("bye_farewellfornow", "generic_quit", "monika_normal"),
        ("bye_untilwemeetagain", "generic_quit", "monika_normal"),
        ("bye_take_care", "generic_quit", "monika_normal"),
    ]

    #(holiday id, messages category, month, day, hour, minute, image)
    FIXED_HOLIDAYS = [
        ("christmas", "holiday_christmas", 12, 25, 0, 0, "monika_normal"),
        ("newyear", "holiday_newyear", 1, 1, 0, 0, "monika_normal"),
        ("valentines", "holiday_valentines", 2, 14, 9, 0, "monika_blushing"),
        ("halloween", "holiday_halloween", 10, 31, 6, 30, "monika_normal"),
        ("aprilfools", "holiday_aprilfools", 4, 1, 6, 30, "monika_wink"),
        ("monika_birthday", "holiday_monika_birthday", 9, 22, 0, 0, "monika_wink"),
    ]

    HOLIDAY_ID_PREFIX = "android_notifs_"

    def _holidayIds():
        """
        Gets the ids of all the holidays of this submod
        """
        return [HOLIDAY_ID_PREFIX + holiday[0] for holiday in FIXED_HOLIDAYS] + [
            HOLIDAY_ID_PREFIX + "player_birthday",
            HOLIDAY_ID_PREFIX + "anniversary",
            HOLIDAY_ID_PREFIX + "test",
        ]

    def _testHolidayDT():
        """
        Gets when the test holiday is shown (test mode only)

        OUT:
            datetime TEST_HOLIDAY_MINUTES from now
        """
        return datetime.datetime.now() + datetime.timedelta(minutes=TEST_HOLIDAY_MINUTES)

    #Minutes until the test holiday (test mode only)
    TEST_HOLIDAY_MINUTES = 10

    def _isSupported():
        """
        Checks if this MAS can show notifications. Only the Android port has the functions of the
        notification framework, on PC (or an old port) the submod stays quiet instead of failing
        """
        return (
            renpy.android
            and hasattr(store, "mas_register_farewell_notification")
            and hasattr(store, "mas_register_holiday_notification")
        )

    def registerNotifs():
        """
        Registers all the notifications of this submod using the current settings
        """
        if not _isSupported():
            return

        for label, category, delay_key, image, alarm in NORMAL_FAREWELLS:
            store.mas_register_farewell_notification(
                label,
                _farewellMessages(category),
                _delaySeconds(delay_key),
                image_path=getImage(image),
                alarm=alarm
            )

        store.mas_register_farewell_notification(
            "bye_prompt_eat",
            _foodMessages,
            _delaySeconds("eat_minutes"),
            image_path=getImage("monika_normal")
        )

        for label in ("bye_prompt_sleep", "bye_going_to_sleep"):
            store.mas_register_farewell_notification(
                label,
                _farewellMessages("sleep", valentines=False),
                _secondsUntilWakeUp,
                image_path=getImage("monika_rousing"),
                alarm=True
            )

        for label, category, image in INTERACTIVE_FAREWELLS:
            store.mas_register_farewell_notification(
                label,
                _farewellMessages(category),
                _delaySeconds("interactive_minutes"),
                is_interactive=True,
                image_path=getImage(image),
                followup_messages=FOLLOWUPS if config["followups_enabled"] else None,
                followup_delay_seconds=config["followup_seconds"]
            )

        if not config["holidays_enabled"]:
            for holiday_id in _holidayIds():
                store.mas_holiday_notif_db.pop(holiday_id, None)
            return

        for holiday_id, category, month, day, hour, minute, image in FIXED_HOLIDAYS:
            store.mas_register_holiday_notification(
                HOLIDAY_ID_PREFIX + holiday_id,
                MESSAGES[category],
                month=month,
                day=day,
                hour=hour,
                minute=minute,
                image_path=getImage(image),
                alarm=True
            )

        store.mas_register_holiday_notification(
            HOLIDAY_ID_PREFIX + "player_birthday",
            MESSAGES["holiday_player_birthday"],
            date_func=_nextPlayerBday,
            hour=0,
            minute=0,
            image_path=getImage("monika_wink"),
            alarm=True
        )

        store.mas_register_holiday_notification(
            HOLIDAY_ID_PREFIX + "anniversary",
            MESSAGES["holiday_anniversary"],
            date_func=_nextAnniversary,
            hour=6,
            minute=30,
            image_path=getImage("monika_blushing"),
            alarm=True
        )

        #Test holiday, so scheduled notifications can be tested without waiting for a real date
        if config["test_mode"]:
            store.mas_register_holiday_notification(
                HOLIDAY_ID_PREFIX + "test",
                MESSAGES["holiday_monika_birthday"],
                date_func=_testHolidayDT,
                image_path=getImage("monika_wink"),
                alarm=True,
                allow_today=True
            )

        else:
            store.mas_holiday_notif_db.pop(HOLIDAY_ID_PREFIX + "test", None)

init 5 python in android_notifs:
    loadConfig()
    registerNotifs()

#START: Settings screens
#Shown in the Submods menu
screen android_notifs_settings():
    vbox:
        box_wrap False
        xfill True
        xmaximum 1000
        style_prefix "check"

        if not renpy.android:
            text _("These notifications only work on Android.") text_align 0.0

        textbutton _("Settings"):
            action Show("android_notifs_config")
            foreground None
            padding (0, 4, 4, 4)

#Settings window, opened from the Submods menu
screen android_notifs_config():
    modal True
    zorder 200

    style_prefix "confirm"
    add mas_getTimeFile("gui/overlay/confirm.png")

    key "game_menu" action Hide("android_notifs_config")

    frame:
        vbox:
            xalign 0.5
            yalign 0.5
            spacing 10

            label _("Android Notifications"):
                style "confirm_prompt"
                xalign 0.5

            if not renpy.android:
                text _("These notifications only work on Android.") style "confirm_prompt_text" xalign 0.5

            null height 5

            vbox:
                #check_vbox has a fixed width (pref_vbox), which wraps the text
                style "vbox"
                style_prefix "check"
                spacing 5

                textbutton _("Holiday notifications"):
                    action Function(store.android_notifs.toggleSetting, "holidays_enabled")
                    selected store.android_notifs.config["holidays_enabled"] and renpy.android
                    sensitive renpy.android

                textbutton _("Follow-ups after you reply"):
                    action Function(store.android_notifs.toggleSetting, "followups_enabled")
                    selected store.android_notifs.config["followups_enabled"] and renpy.android
                    sensitive renpy.android

            null height 5
            text _("Notification time after each farewell:") style "confirm_prompt_text" text_align 0.0

            for _key, _label in store.android_notifs.TIME_SETTINGS:
                use android_notifs_time_setting(_key, _label)

            if store.android_notifs.config["followups_enabled"]:
                use android_notifs_time_setting("followup_seconds", _("Time between follow-ups"))

            null height 10
            textbutton _("Close"):
                action Hide("android_notifs_config")
                xalign 0.5

#A row to pick a time setting: < value > label
screen android_notifs_time_setting(setting_key, setting_label):
    hbox:
        spacing 10

        textbutton "<":
            style "check_button"
            text_style "check_button_text"
            foreground None
            padding (8, 4, 8, 4)
            action Function(store.android_notifs.cycleSetting, setting_key, -1)
            sensitive renpy.android

        text store.android_notifs.formatSetting(setting_key):
            style "confirm_prompt_text"
            yalign 0.5
            min_width 140

        textbutton ">":
            style "check_button"
            text_style "check_button_text"
            foreground None
            padding (8, 4, 8, 4)
            action Function(store.android_notifs.cycleSetting, setting_key, 1)
            sensitive renpy.android

        text setting_label:
            style "confirm_prompt_text"
            text_align 0.0
            yalign 0.5

#START: App reactions (Android only)
#Apps MAS doesn't react to by default. PC is skipped with the conditional
init 5 python:
    for _app_id, _app_name, _app_packages in [
        ("tiktok", "TikTok", ["com.zhiliaoapp.musically", "com.ss.android.ugc.trill"]),
        ("youtubemusic", "YouTube Music", ["com.google.android.apps.youtube.music"]),
        ("instagram", "Instagram", ["com.instagram.android"]),
        ("facebook", "Facebook", ["com.facebook.katana", "com.facebook.lite"]),
        ("spotify", "Spotify", ["com.spotify.music"]),
        ("messenger", "Messenger", ["com.facebook.orca"]),
        ("applemusic", "Apple Music", ["com.apple.android.music"]),
        ("discord", "Discord", ["com.discord"]),
        ("telegram", "Telegram", ["org.telegram.messenger"]),
        ("steam", "Steam", ["com.valvesoftware.android.steam.community"]),
        ("whatsapp", "WhatsApp", ["com.whatsapp", "com.whatsapp.w4b"]),
    ]:
        addEvent(
            Event(
                persistent._mas_windowreacts_database,
                eventlabel="android_notifs_wrs_" + _app_id,
                category=[_app_name] + _app_packages,
                conditional="renpy.android",
                rules={
                    "notif-group": "Window Reactions",
                    "skip alert": None,
                    "keep_idle_exp": None,
                    "skip_pause": None
                },
                show_in_idle=True
            ),
            code="WRS"
        )

label android_notifs_wrs_tiktok:
    call android_notifs_app_reaction("tiktok")
    return

label android_notifs_wrs_youtubemusic:
    call android_notifs_app_reaction("youtubemusic")
    return

label android_notifs_wrs_instagram:
    call android_notifs_app_reaction("instagram")
    return

label android_notifs_wrs_facebook:
    call android_notifs_app_reaction("facebook")
    return

label android_notifs_wrs_spotify:
    call android_notifs_app_reaction("spotify")
    return

label android_notifs_wrs_messenger:
    call android_notifs_app_reaction("messenger")
    return

label android_notifs_wrs_applemusic:
    call android_notifs_app_reaction("applemusic")
    return

label android_notifs_wrs_discord:
    call android_notifs_app_reaction("discord")
    return

label android_notifs_wrs_telegram:
    call android_notifs_app_reaction("telegram")
    return

label android_notifs_wrs_steam:
    call android_notifs_app_reaction("steam")
    return

label android_notifs_wrs_whatsapp:
    call android_notifs_app_reaction("whatsapp")
    return

label android_notifs_app_reaction(app_id):
    $ wrs_success = mas_display_notif(
        m_name,
        android_notifs.APP_MESSAGES[app_id],
        'Window Reactions',
        image_path=android_notifs.getImage("monika_normal")
    )

    #Unlock again if we failed
    if not wrs_success:
        $ mas_unlockFailedWRS("android_notifs_wrs_" + app_id)
    return
