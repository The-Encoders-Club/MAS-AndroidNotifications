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
