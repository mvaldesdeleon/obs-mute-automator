import obspython as obs
import pprint as pp

debug = True

# ------------------------------------------------------------

def dprint(*input):
    if debug == True:
        print(*input)

# ------------------------------------------------------------

mute_indicator = ''

def list_video_sources():
    video_sources = []
    sources = obs.obs_enum_sources()

    for source in sources:
        if obs.obs_source_get_type(source) == obs.OBS_SOURCE_TYPE_INPUT:
            capabilities = obs.obs_source_get_output_flags(source)
            has_video = capabilities & obs.OBS_SOURCE_VIDEO

            if has_video:
                video_sources.append(obs.obs_source_get_name(source))

    obs.source_list_release(sources)

    return video_sources

# ------------------------------------------------------------

main_microphone = 'AT2035'

def list_audio_sources():
    audio_sources = []
    sources = obs.obs_enum_sources()

    for source in sources:
        if obs.obs_source_get_type(source) == obs.OBS_SOURCE_TYPE_INPUT:
            capabilities = obs.obs_source_get_output_flags(source)
            has_audio = capabilities & obs.OBS_SOURCE_AUDIO

            if has_audio:
                audio_sources.append(obs.obs_source_get_name(source))

    obs.source_list_release(sources)

    return audio_sources

monitored_source = None

def update_mute_indicator(muted):
    if not mute_indicator:
        return

    source = obs.obs_get_source_by_name(mute_indicator)
    if not source:
        dprint(f'Error! Could not get source {mute_indicator}')
        return

    obs.obs_source_set_enabled(source, muted)

    obs.obs_source_release(source)

def mute_callback(calldata):
    muted = obs.calldata_bool(calldata, 'muted')
    status = 'muted' if muted else 'unmuted'

    dprint(f'Main microphone {status}')

    update_mute_indicator(muted)

def remove_muted_callback(name):
    if not name:
        return

    source = obs.obs_get_source_by_name(name)
    if not source:
        dprint(f'Error! Could not get source {name}')
        return

    handler = obs.obs_source_get_signal_handler(source)
    obs.signal_handler_disconnect(handler, 'mute', mute_callback)

    dprint(f'Removed mute callback for {name}')

    obs.obs_source_release(source)

    return True

def create_muted_callback(name):
    global monitored_source

    if not name or monitored_source == name:
        return

    if monitored_source:
        remove_muted_callback(monitored_source)

    source = obs.obs_get_source_by_name(name)
    if not source:
        dprint(f'Error! Could not get source {name}')
        return

    handler = obs.obs_source_get_signal_handler(source)
    obs.signal_handler_connect(handler, 'mute', mute_callback)
    monitored_source = name

    dprint(f'Added mute callback for {name}')

    muted = obs.obs_source_muted(source)
    status = 'muted' if muted else 'unmuted'

    dprint(f'Main microphone {status}')

    update_mute_indicator(muted)

    obs.obs_source_release(source)


# ------------------------------------------------------------

header_decorator = '--------'
header_pattern = '- '

scenes = {}
scenes_loaded = False

def is_header(name):
    return name.startswith(header_decorator)

def get_header_name(name):
    return name.strip(header_pattern)

def get_scene_key(name):
    return name.lower().replace(' ', '-')

def get_header_key(name):
    return get_scene_key(get_header_name(name))

def fetch_scenes():
    global scenes

    fetched = False
    
    sources = obs.obs_frontend_get_scenes()
    if sources:
        fetched = True
    scene_names = [obs.obs_source_get_name(source) for source in sources]
    obs.source_list_release(sources)

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

def try_fetch_scenes():
    global scenes_loaded

    if fetch_scenes():
        obs.remove_current_callback()
        scenes_loaded = True
        create_muted_callback(main_microphone)

# ------------------------------------------------------------

def frontend_cb(event):
    if event == obs.OBS_FRONTEND_EVENT_SCENE_CHANGED:
        source = obs.obs_frontend_get_current_scene()
        name = obs.obs_source_get_name(source)
        key = get_scene_key(name)

        if is_header(name):
            dprint(f'Warning! Changed to header scene: {get_header_key(name)}')
        elif key in scenes:
            header_key = scenes[key]
            dprint(f'Scene changed: {header_key}, {key}')
        else:
            dprint(f'Warning! Changed to a scene with no header: {key}')

        obs.obs_source_release(source)

# ------------------------------------------------------------

def script_load(settings):
    obs.obs_frontend_add_event_callback(frontend_cb)
    obs.timer_add(try_fetch_scenes, 500)

def script_unload():
    obs.timer_remove(try_fetch_scenes)
    if monitored_source is not None:
        remove_muted_callback(monitored_source)
    obs.obs_frontend_remove_event_callback(frontend_cb)

def script_description():
    return '<b>OBS Mute Automator</b>' + \
        '<hr>' + \
        'Automatically enabling push-to-talk when switching into title scenes, ' + \
        'as well as automatically toggling a target source\'s visibility when \'mute\' is enabled.' + \
        '<br/><br/>' + \
        '<a href="http://github.com/mvaldesdeleon/obs-mute-automator">github.com/mvaldesdeleon/obs-mute-automator</a>'

def script_update(settings):
    global header_decorator, header_pattern, main_microphone, mute_indicator, debug

    header_decorator = obs.obs_data_get_string(settings, 'header-decorator')
    header_pattern = obs.obs_data_get_string(settings, 'header-pattern')
    main_microphone = obs.obs_data_get_string(settings, 'main-microphone')
    mute_indicator = obs.obs_data_get_string(settings, 'mute-indicator')
    debug = obs.obs_data_get_bool(settings, 'debug')

    if scenes_loaded:
        create_muted_callback(main_microphone)

def script_defaults(settings):
    obs.obs_data_set_default_string(settings, 'header-decorator', header_decorator)
    obs.obs_data_set_default_string(settings, 'header-pattern', header_pattern)
    obs.obs_data_set_default_string(settings, 'main-microphone', main_microphone)
    obs.obs_data_set_default_string(settings, 'mute-indicator', mute_indicator)
    obs.obs_data_set_default_bool(settings, 'debug', debug)

def script_properties():
    props = obs.obs_properties_create()

    obs.obs_properties_add_text(props, 'header-decorator', 'Header decorator', obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(props, 'header-pattern', 'List of characters used in the decorator', obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_button(props, 'reload-scenes', 'Reload scenes', lambda *args: fetch_scenes())

    audio_source_list = obs.obs_properties_add_list(props, 'main-microphone', 'Main microphone', obs.OBS_COMBO_TYPE_LIST, obs.OBS_COMBO_FORMAT_STRING)
    for name in list_audio_sources():
        obs.obs_property_list_add_string(audio_source_list, name, name)

    video_source_list = obs.obs_properties_add_list(props, 'mute-indicator', 'Mute indicator', obs.OBS_COMBO_TYPE_LIST, obs.OBS_COMBO_FORMAT_STRING)
    for name in list_video_sources():
        obs.obs_property_list_add_string(video_source_list, name, name)

    obs.obs_properties_add_bool(props, 'debug', 'Print Debug Messages')
    
    return props