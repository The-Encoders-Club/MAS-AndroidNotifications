init -990 python in mas_submod_utils:
    Submod(
        author="Slytharbez",
        name="Android Notifications",
        description=_("Monika sends you notifications on Android when you leave with a farewell, on holidays, and when you open some apps."),
        version="1.0.1",
        settings_pane="android_notifs_settings"
    )

# Updates through the Submod Updater Plugin. It is optional: without it the submod works the same
# NOTE: the tag of each release on GitHub has to be the version above (e.g. 1.0.1, a leading v is ignored)
init -989 python:
    if store.mas_submod_utils.isSubmodInstalled("Submod Updater Plugin"):
        store.sup_utils.SubmodUpdater(
            submod="Android Notifications",
            user_name="The-Encoders-Club",
            repository_name="MAS-AndroidNotifications",
            tag_formatter=lambda tag: tag.lstrip("vV")
        )

# The pane of the Submods menu. The real settings are in android_notifications.rpy (android_notifs_settings_main).
# If that file is missing or is from another version (an incomplete or mixed install) this screen still exists,
# so the Submods menu keeps working and tells what to do, instead of stopping with "Screen is not known"
screen android_notifs_settings():
    if renpy.has_screen("android_notifs_settings_main"):
        use android_notifs_settings_main

    else:
        vbox:
            box_wrap False
            xfill True
            xmaximum 1000
            style_prefix "check"

            text _("Android Notifications is not installed correctly: android_notifications.rpy is missing or is from another version.") text_align 0.0
            text _("Delete the Android Notifications folder, extract the zip again and restart the game.") text_align 0.0
