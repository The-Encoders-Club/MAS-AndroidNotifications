# Android Notifications

The official notifications submod for the Android port of Monika After Story (MAS).

Monika sends you notifications on your phone when:
- you say goodbye to her (going to class, to work, shopping, to eat, to work out, to play, and so on) and you take a while to come back,
- a special date arrives (Christmas, New Year, Valentine's Day, Halloween, Monika's birthday, your birthday and your anniversaries),
- you open certain apps while MAS is in picture-in-picture mode or a floating window.

**It only does something in the Android port of MAS.** On PC it installs without problems, but it does nothing.

---

## Requirements

- The Android port of MAS, which includes the notification functions of the core (`mas_register_farewell_notification`, `mas_register_holiday_notification` and `mas_display_notif`).
- The notifications permission for the app. For the app reactions, also the usage access or accessibility permission (the app asks for it).
- Optional: [Submod Updater Plugin](https://github.com/Booplicate/MAS-Submods-SubmodUpdaterPlugin), to update this submod from inside the game.
  - It is optional on purpose: without it the submod works the same and is updated by hand.
  - On Android you do not need the plugin's `lib` folder (it holds SSL files for Windows, Linux and Mac, and the port already ships its own SSL). Copy only its `game` folder.
  - If you would rather require it, add `dependencies={"Submod Updater Plugin": ("1.0.0", "99.99.99")}` to the `Submod(...)` block. MAS will then not load this submod without the plugin.

---

## Installation

1. Download the latest `Android Notifications.zip` from [Releases](https://github.com/The-Encoders-Club/NotifSubmodTemplate/releases/latest).
2. Extract it inside the `game/Submods/` folder of Monika After Story.
   - On Android the folder is `Internal storage/Monika After Story/game/Submods/`.
   - On PC it is `DDLC/game/Submods/`.
3. It has to end up like this:
   ```
   game/Submods/Android Notifications/
   ├── android_notifications.rpy            (the submod and its settings)
   ├── android_notifications_messages.rpy   (the messages)
   ├── notif/                               (the avatars, PNG)
   └── tl/
       └── spanish/
           └── android_notifications_es.rpy (Spanish translation)
   ```
4. Open the game. In **Settings, Submods, Android Notifications** you can choose how long Monika waits before writing to you.

The first time it runs, the submod creates a `config.json` file in its folder with your settings. You do not need to edit it by hand.

### Updating

- **With Submod Updater Plugin installed:** the game tells you when there is a new version and downloads it from here. Restart the game to apply it.
- **By hand:** download the new zip and extract it over the old one, overwriting. Your settings (`config.json`) are kept.

If you installed a test version that kept `android_notifications_es.rpy` next to the main file (outside `tl/spanish/`), delete that one and its `.rpyc`: two copies of the same translation make Ren'Py complain about a duplicate.

---

## Settings

Every time is chosen in the game. Default values:

| Setting | Default | Options |
|---|---|---|
| Going to class | 7 h | 3 to 8 h |
| Going to work | 8 h | 4 to 10 h |
| Going shopping | 30 min | 15 min to 2 h |
| Going to eat | 25 min | 15 to 60 min |
| Wake up time | 6:00 | 5:00 to 10:00 |
| Other farewells | 3 h | 15 min to 3 h |
| Follow-up message | 30 s | 15 s to 3 min |
| Follow-up messages | on | on / off |
| Special dates | on | on / off |

When you open the game, the farewell notifications that were still pending are cancelled. The special dates are cancelled only if it is that very day.

### Test mode (development only)

If you set `"test_mode": true` in `config.json`, minutes count as seconds and a test holiday is added 10 minutes from now. It lets you check that notifications arrive without waiting. It is not shown in the settings. **Leave it `false` (or remove the line) for normal use.**

---

## How it works (short version)

- Normal notifications (the ones with a wait: class, work, shopping, food) are scheduled when you say goodbye, have no reply button, and open MAS when tapped.
- The interactive ones (the other farewells) have a **Reply** button and chained follow-up messages.
- `alarm=True` makes a notification behave like an alarm, so some phone brands (MIUI, for example) do not silence it with the screen off.
- The preferences of this submod are not stored in `persistent`: they use their own `config.json`.
- A notification without an image uses the app icon, never an image of Monika.

---

## Publishing a version (for maintainers)

1. Raise the `version` in the `Submod(...)` block of `android_notifications.rpy`.
2. Make a zip that contains the whole `Android Notifications` folder (with the `.rpy` files, `notif/` and `tl/`; **without** `config.json` or `.rpyc` files).
3. On GitHub, create a **Release** whose **tag is the same as the version** (for example `1.0.1`) and attach that zip as the **only file**. That is what Submod Updater Plugin downloads.
4. The plugin checks GitHub at most once an hour.

---

## License

MIT. Copyright (c) 2026 The Encoders Club.
