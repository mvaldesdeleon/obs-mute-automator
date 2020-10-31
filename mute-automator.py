import obspython as obs
import pprint as pp

# User properties
main_microphone = ''
mute_indicator = ''
header_decorator = '--------'
header_pattern = '- '
push_to_talk_key = 'title-scenes'
debug = True

# Internal globals
scenes_loaded = False
scenes = {}
active_main_microphone = ''
active_mute_indicator = ''
push_to_talk = False

def dprint(*input):
    """Print debugging messages if required"""
    if debug == True:
        print(*input)

def list_sources(flags=None):
    """"List sources, optionally filtering by the provided output flags"""
    result = []
    sources = obs.obs_enum_sources()

    for source in sources:
        if obs.obs_source_get_type(source) == obs.OBS_SOURCE_TYPE_INPUT:
            capabilities = obs.obs_source_get_output_flags(source)
            
            if flags is None or capabilities & flags:
                result.append(obs.obs_source_get_name(source))    

    obs.source_list_release(sources)

    return result

def list_video_sources():
    """List video sources"""
    return list_sources(obs.OBS_SOURCE_VIDEO)

def list_audio_sources():
    """List audio sources"""
    return list_sources(obs.OBS_SOURCE_AUDIO)

def restore_mute_indicator(mute_indicator):
    """Restore the provided source"""
    set_mute_indicator(mute_indicator, True)

def set_mute_indicator(mute_indicator, enabled):
    """Toggle the provided source"""
    if not mute_indicator:
        return

    source = obs.obs_get_source_by_name(mute_indicator)
    if not source:
        dprint(f'Error! Could not get source {mute_indicator}')
        return

    obs.obs_source_set_enabled(source, enabled)

    obs.obs_source_release(source)

def update_mute_indicator(mute_indicator, main_microphone):
    """Update the mute indicator to reflect the current mute status of the main microphone"""
    if not main_microphone:
        return

    source = obs.obs_get_source_by_name(main_microphone)
    muted = obs.obs_source_muted(source)
    status = 'muted' if muted else 'unmuted'

    dprint(f'Main microphone {status}')

    set_mute_indicator(mute_indicator, muted)

    obs.obs_source_release(source)

def mute_callback(calldata):
    """Process mute and unmute events"""
    muted = obs.calldata_bool(calldata, 'muted')
    status = 'muted' if muted else 'unmuted'

    dprint(f'Main microphone {status}')

    set_mute_indicator(active_mute_indicator, muted)

def remove_mute_callback(main_microphone):
    """Removes mute callback from the provided source"""
    if not main_microphone:
        return

    source = obs.obs_get_source_by_name(main_microphone)
    if not source:
        dprint(f'Error! Could not get source {main_microphone}')
        return

    handler = obs.obs_source_get_signal_handler(source)
    obs.signal_handler_disconnect(handler, 'mute', mute_callback)

    dprint(f'Removed mute callback from {main_microphone}')

    obs.obs_source_release(source)

    return True

def create_mute_callback(main_microphone):
    """Creates mute callback for the provided source"""
    if not main_microphone:
        return

    source = obs.obs_get_source_by_name(main_microphone)
    if not source:
        dprint(f'Error! Could not get source {main_microphone}')
        return

    handler = obs.obs_source_get_signal_handler(source)
    obs.signal_handler_connect(handler, 'mute', mute_callback)
    
    dprint(f'Added mute callback for {main_microphone}')

    obs.obs_source_release(source)

def restore_push_to_talk(main_microphone):
    """Restore the provided source"""
    if push_to_talk:
        set_push_to_talk(main_microphone, False)

def set_push_to_talk(main_microphone, enabled):
    """Sets Push-to-talk on the provided source"""
    if not main_microphone:
        return

    source = obs.obs_get_source_by_name(main_microphone)
    if not source:
        dprint(f'Error! Could not get source {main_microphone}')
        return

    obs.obs_source_enable_push_to_talk(source, enabled)
    
    status = 'enabled' if enabled else 'disabled'
    dprint(f'Push to talk {status}')

    obs.obs_source_release(source)

def update_push_to_talk(main_microphone, enabled):
    """Update Push-to-talk on the provided source"""
    global push_to_talk

    if enabled == push_to_talk:
        return
    
    set_push_to_talk(main_microphone, enabled)
    push_to_talk = enabled

def is_header(name):
    """Checks if a given Scene is a Header/Separator scene"""
    return name.startswith(header_decorator)

def get_header_name(name):
    """Extract the name from a Header/Separator scene"""
    return name.strip(header_pattern)

def get_scene_key(name):
    """Extract the Scene Key from a Scene"""
    return name.lower().replace(' ', '-')

def get_header_key(name):
    """Extract the Header key from a Header/Separator scene"""
    return get_scene_key(get_header_name(name))

def fetch_scenes():
    """Fetch Scenes and process Header/Separator hierarchy"""
    global scenes

    fetched = False
    
    sources = obs.obs_frontend_get_scenes()
    if sources:
        fetched = True
    scene_names = [obs.obs_source_get_name(source) for source in sources]
    obs.source_list_release(sources)

    scenes = {}
    current_key = None
    for name in scene_names:
        if is_header(name):
            current_key = get_header_key(name)
        elif current_key != None:
            scenes[get_scene_key(name)] = current_key
        else:
            dprint(f'Could not process scene {name}')

    dprint(f'{pp.pformat(scenes)}')

    return fetched

def reload_scenes(property, data):
    fetch_scenes()
    check_current_scene()

def try_fetch_scenes():
    """Attempt to fetch the scenes"""
    global scenes_loaded, active_main_microphone, active_mute_indicator

    if fetch_scenes():
        scenes_loaded = True
        obs.remove_current_callback()
        active_main_microphone = main_microphone
        active_mute_indicator = mute_indicator
        # Mute indicator
        create_mute_callback(main_microphone)
        update_mute_indicator(mute_indicator, main_microphone)
        # Push-to-talk
        check_current_scene()

def check_current_scene():
    """Check the current scene and update Push-to-talk on the main microphone accordingly"""
    source = obs.obs_frontend_get_current_scene()
    name = obs.obs_source_get_name(source)
    key = get_scene_key(name)

    if is_header(name):
        dprint(f'Warning! Changed to header scene: {get_header_key(name)}')
    elif key in scenes:
        header_key = scenes[key]
        dprint(f'Scene changed: {header_key}, {key}')

        update_push_to_talk(active_main_microphone, header_key == push_to_talk_key)
    else:
        dprint(f'Warning! Changed to a scene with no header: {key}')

    obs.obs_source_release(source)

def frontend_event_callback(event):
    """Process frontend events"""
    if scenes_loaded and event == obs.OBS_FRONTEND_EVENT_SCENE_CHANGED:
        check_current_scene()

def script_load(settings):
    # Setup global timers/callbacks
    obs.obs_frontend_add_event_callback(frontend_event_callback)
    obs.timer_add(try_fetch_scenes, 500)

def script_unload():
    # Remove all timers/callbacks
    obs.timer_remove(try_fetch_scenes)
    obs.obs_frontend_remove_event_callback(frontend_event_callback)
    remove_mute_callback(active_main_microphone)
    # Restore active sources
    restore_push_to_talk(active_main_microphone)
    restore_mute_indicator(active_mute_indicator)

def script_description():
    return '<b>OBS Mute Automator</b>' + \
        '<hr>' + \
        'Automatically enabling push-to-talk when switching into title scenes, ' + \
        'as well as automatically toggling a target source\'s visibility when \'mute\' is enabled.' + \
        '<br/><br/>' + \
        '<a href="https://github.com/mvaldesdeleon/obs-mute-automator">https://github.com/mvaldesdeleon/obs-mute-automator</a>'

def script_update(settings):
    global main_microphone, mute_indicator, header_decorator, header_pattern, push_to_talk_key, debug, push_to_talk, active_main_microphone, active_mute_indicator

    main_microphone = obs.obs_data_get_string(settings, 'main-microphone')
    mute_indicator = obs.obs_data_get_string(settings, 'mute-indicator')
    header_decorator = obs.obs_data_get_string(settings, 'header-decorator')
    header_pattern = obs.obs_data_get_string(settings, 'header-pattern')
    push_to_talk_key = obs.obs_data_get_string(settings, 'push-to-talk-key')
    debug = obs.obs_data_get_bool(settings, 'debug')

    if scenes_loaded:
        if main_microphone and main_microphone != active_main_microphone:
            remove_mute_callback(active_main_microphone)
            restore_push_to_talk(active_main_microphone)
            push_to_talk = False
            active_main_microphone = main_microphone
            create_mute_callback(main_microphone)
            update_mute_indicator(mute_indicator, main_microphone)
        if mute_indicator and mute_indicator != active_mute_indicator:
            restore_mute_indicator(active_mute_indicator)
            active_mute_indicator = mute_indicator
            update_mute_indicator(mute_indicator, main_microphone)
        fetch_scenes()
        check_current_scene()

def script_defaults(settings):
    obs.obs_data_set_default_string(settings, 'main-microphone', main_microphone)
    obs.obs_data_set_default_string(settings, 'mute-indicator', mute_indicator)
    obs.obs_data_set_default_string(settings, 'header-decorator', header_decorator)
    obs.obs_data_set_default_string(settings, 'header-pattern', header_pattern)
    obs.obs_data_set_default_string(settings, 'push-to-talk-key', push_to_talk_key)
    obs.obs_data_set_default_bool(settings, 'debug', debug)

def script_properties():
    props = obs.obs_properties_create()

    audio_source_list = obs.obs_properties_add_list(props, 'main-microphone', 'Main microphone', obs.OBS_COMBO_TYPE_LIST, obs.OBS_COMBO_FORMAT_STRING)
    for name in list_audio_sources():
        obs.obs_property_list_add_string(audio_source_list, name, name)

    video_source_list = obs.obs_properties_add_list(props, 'mute-indicator', 'Mute indicator', obs.OBS_COMBO_TYPE_LIST, obs.OBS_COMBO_FORMAT_STRING)
    for name in list_video_sources():
        obs.obs_property_list_add_string(video_source_list, name, name)

    obs.obs_properties_add_text(props, 'header-decorator', 'Header decorator', obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(props, 'header-pattern', 'List of characters used in the decorator', obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(props, 'push-to-talk-key', 'Header key to enable Push-to-talk', obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_button(props, 'reload-scenes', 'Reload scenes', reload_scenes)

    obs.obs_properties_add_bool(props, 'debug', 'Print debug messages')
    
    return props