# OBS Mute Automator

OBS Mute Automator is a python-based OBS script that provides a couple of automations around muting your main microphone Audio source.

## Mute Indicator

Enable and disable a Video source depending on the mute status of the main microphone Audio source.

## Automatic push-to-talk

Enable and disable Push-to-talk on your main microphone Audio source depending on the current scene.

# Installation

Clone this repository, or just download the [mute-automator.py](https://raw.githubusercontent.com/mvaldesdeleon/obs-mute-automator/mainline/mute-automator.py) file, and add it into OBS via the **Script** dialogue found under the **Tools** menu.

Python scripts require Python to be installed on your computer. Due to [limitations with OBS](https://obsproject.com/docs/scripting.html), at the moment Windows users must install Python 3.6.x. The official download links for the Windows installers for Python 3.6.8 are available [here](https://www.python.org/downloads/release/python-368/).

# Configuration

![Configuration screen](https://raw.githubusercontent.com/mvaldesdeleon/obs-mute-automator/mainline/images/config.png)

**Main microphone**: Audio source to be used as the main microphone.  
**Mute indicator**: Video source to be used as the mute indicator.  
**Header decorator**: Used to identify your Scenes structure. If you use Separator scenes named `### My Separator ###`, then you would use `###` as the decorator.  
**List of characters used in the decorator**: Used to strip down the decorators from the Separator scenes' names. Be sure to include whitespace characters if needed. For the above example, you would use `# ` as the list of characters.  
**Header key to enable Push-to-talk**: Used to enable Push-to-talk when Scenes from this Header are enabled. Separator scenes' names are stripped from separators, lowercased, and spaces are replaced by hyphens. For my current configuration, I use `title-scenes`.  
**Reload scenes**: Click to refresh when updating adding/removing/renaming scenes, or changing the Separator naming convention.  
**Print debug messages**: Log debugging information into the Script Log provided by OBS.

For reference, this is how my current Separator scenes look like:

![Separator scenes](https://raw.githubusercontent.com/mvaldesdeleon/obs-mute-automator/mainline/images/scenes.png)

# Caveats

The push-to-talk capability of OBS does not interact with its mute capability. What this means is that enabling push-to-talk will not trigger the mute indicator.

# Roadmap

* [ ] Increase configurability.
  * [x] Expose header key for enabling push-to-talk.
  * [ ] Offer to toggle the behaviour of the mute indicator so that the Video source is **enabled** when the main microhone Audio source is **unmuted**.
* [ ] Allow enabling/disabling each of the main features.
* [x] Clean-up code.

# License
BSD-3-Clause