"""Single-threaded show state machine; inputs never enqueue playback."""
import bisect
import random
import time

BACKGROUND = 'background_music_final.wav'
ZAP = 'electric-zap_break_final.mp3'
ZAP_UP = 'electric-zap_up_final.mp3'
STAGES = (ZAP, 'church_bell_final.mp3',
          'michael_myers_final.mp3', 'laughing.wav')
VOICES = ('voice_gruen_sein.mp3', 'voice_habt_geduld.mp3')
FILES = (BACKGROUND,) + STAGES + (ZAP_UP,) + VOICES
BLACK = (0, 0, 0, 0)
RED = (255, 0, 0, 0)
GREEN = (0, 255, 0, 0)


def scaled(color, gain):
    return tuple(round(v * gain) for v in color)


class Show:
    def __init__(self, audio, supply, lighting, config, zap_timeline,
                 clock=time.monotonic, choose=random.choice, log=print,
                 up_timeline=None, panic_audio=None, resume_audio=None):
        self.audio, self.supply, self.lighting = audio, supply, lighting
        self.config, self.zap = config, zap_timeline
        self.clock, self.choose, self.log = clock, choose, log
        self.state = 'STOPPED'
        self.stage = 0
        self.voice = False
        self.blink_started = None
        self.event_index = -1
        self.zap_times = [event['time_s'] for event in self.zap['events']]
        self.up = up_timeline
        self.up_times = ([] if up_timeline is None else
                         [event['time_s'] for event in up_timeline['events']])
        self.manual_powering = False
        self.manual_light_on = False
        self.panic_audio = panic_audio
        self.resume_audio = resume_audio
        self.panic_at = 0
        self.panic_release_requested = False
        self.locked_background = False
        self.locked_background_at = None

    def status_color(self, color, fade=True):
        gain = (self.config['par_idle_brightness'] if color == GREEN
                else self.config['status_brightness'])
        target = scaled(color, gain)
        if fade:
            self.lighting.fade_to(target, self.config['transition_s'], self.clock())
        else:
            self.lighting.color(target)

    def start(self):
        self.locked_background = False
        self.locked_background_at = None
        self.supply.bright(fade_s=self.config['transition_s'],
                           current_A=self.config['korad_idle_current_A'])
        self.state = 'IDLE'
        self.status_color(GREEN)
        self.audio.start(BACKGROUND)
        self.log(f'IDLE: Hintergrundmusik, KORAD {self.config["korad_idle_current_A"] * 1000:.0f} mA, Flat Par grün')

    def buzzer(self):
        # This guard also covers the time after manual release while a voice
        # finishes. No restart, queue or overlapping voice/flash sequences.
        if self.voice or self.manual_powering:
            return
        if self.state == 'IDLE':
            self.audio.stop()
            self.state = 'RUNNING'
            self.supply.bright(fade_s=self.config['transition_s'])
            self.stage = 0
            self.begin_stage()
        elif self.state == 'LOCKED' and self.blink_started is None:
            self.stop_locked_background()
            self.voice = True
            self.blink_started = self.clock()
            self.audio.start(self.choose(VOICES))
            self.lighting.color(BLACK)

    def release(self, pressed_at=None):
        if self.state == 'PANIC':
            if pressed_at is not None and pressed_at <= self.panic_at:
                return
            self.panic_release_requested = True
            self.resume_from_panic()
            return
        # A release during RUNNING must not pre-arm the next show.
        if self.state != 'LOCKED':
            return
        if not self.manual_powering:
            self.supply.bright(fade_s=self.config['transition_s'],
                               current_A=self.config['korad_idle_current_A'])
        self.blink_started = None
        self.status_color(GREEN)
        if self.voice or self.manual_powering:
            self.state = 'RELEASING'
            self.log('Freigabe: grün; laufende Audiodatei endet zuerst')
        else:
            self.state = 'IDLE'
            if not self.locked_background or self.audio.done():
                self.audio.start(BACKGROUND)
            self.locked_background = False
            self.locked_background_at = None
            self.log('IDLE: manuell freigegeben')

    def panic(self):
        self.state = 'PANIC'
        self.panic_at = time.time()
        self.panic_release_requested = False
        self.locked_background = False
        self.locked_background_at = None
        self.voice = False
        self.manual_powering = False
        self.manual_light_on = False
        self.blink_started = None
        self.pause_until = None
        # Attempt every action even if one device is unavailable.
        actions = [('HEOS', self.panic_audio),
                   ('PAR', self.lighting.blackout_now),
                   ('Audio', self.audio.stop),
                   ('KORAD', lambda: self.supply.bright(
                       current_A=self.config['korad_idle_current_A']))]
        for name, action in actions:
            if action is not None:
                try:
                    action()
                except Exception as error:
                    self.log(f'PANIC: {name} konnte nicht umgestellt werden: {error}')
        self.log('PANIC: alles gestoppt, nur KORAD 300 mA; Freigabe mit Taste 1')

    def enter_locked(self):
        self.state = 'LOCKED'
        self.manual_light_on = False
        self.locked_background = False
        self.locked_background_at = self.clock() + self.config['locked_background_delay_s']
        self.status_color(RED)
        self.log('LOCKED: rot; Freigabe nur über Hama-Taste 1')

    def stop_locked_background(self):
        if self.locked_background:
            self.audio.stop()
            self.locked_background = False

    def finish(self, pressed_at=None):
        """Key 2 selects the same locked mode as the regular show ending."""
        if self.state in ('PANIC', 'STOPPED'):
            return
        if pressed_at is not None and pressed_at <= self.panic_at:
            return
        # A voice response must still finish fully. Operator mode selection
        # can abort main-show/background audio and the manual power-up effect.
        if not self.voice:
            self.audio.stop()
        self.manual_powering = False
        self.blink_started = None
        self.pause_until = None
        self.supply.off(fade_s=self.config['transition_s'])
        self.enter_locked()

    def resume_from_panic(self):
        if self.resume_audio is not None and not self.resume_audio():
            return
        self.panic_release_requested = False
        self.start()

    def power(self):
        """Play/Pause toggles only the KORAD lamp while the show is locked."""
        if (self.state != 'LOCKED' or self.voice or self.manual_powering
                or self.blink_started is not None):
            return
        if self.manual_light_on:
            self.supply.off(fade_s=self.config['transition_s'])
            self.manual_light_on = False
            self.log('LOCKED: KORAD manuell aus; Show bleibt gesperrt')
        else:
            if not self.up_times:
                raise RuntimeError('Power-up audio timeline is unavailable')
            self.stop_locked_background()
            self.supply.bright(current_A=.001)
            self.audio.start(ZAP_UP)
            self.up_started = self.clock()
            self.up_index = -1
            self.manual_powering = True
            self.log('LOCKED: KORAD einschalten mit Zap-up; Show bleibt gesperrt')

    def begin_stage(self):
        self.event_index = -1
        self.zap_fading = False
        self.pause_until = None
        if self.stage == 2:
            self.lighting.color(BLACK)
        else:
            self.lighting.fade_to(BLACK, self.config['transition_s'], self.clock())
        self.audio.start(STAGES[self.stage])
        self.stage_started = self.clock()
        if self.stage == 0:
            duration = self.config['zap_par_flash_s']
            fade_out = self.config['zap_par_flash_fade_s']
            self.lighting.flash_at((255, 255, 255, 0),
                                   [max(0, self.zap['duration_s'] - duration - fade_out
                                        - self.config['zap_par_flash_advance_s'])],
                                   self.stage_started, duration, fade_out, preserve_fade=True)
        elif self.stage == 1:
            cfg = self.config['bell_lighting']
            self.lighting.flash_at(cfg['color'], cfg['gong_times_s'],
                                   self.stage_started, cfg['hold_s'], cfg['fade_out_s'])
        self.log('RUNNING: ' + STAGES[self.stage])

    def tick(self):
        now = self.clock()
        if self.state == 'PANIC':
            if self.panic_release_requested:
                self.resume_from_panic()
            self.supply.tick(now)
            self.lighting.tick(now)
            return
        if self.manual_powering:
            if self.audio.done():
                self.manual_powering = False
                self.manual_light_on = True
                self.supply.bright(fade_s=self.config['transition_s'],
                                   current_A=self.config['korad_idle_current_A'])
                self.log('KORAD: Einschalteffekt fertig, 300 mA')
            else:
                index = bisect.bisect_right(self.up_times, now - self.up_started) - 1
                if index >= 0 and index != self.up_index:
                    self.supply.current(self.up['events'][index]['current_A'])
                    self.up_index = index
        if self.state == 'IDLE':
            if self.audio.done():
                self.audio.start(BACKGROUND)
        elif self.state == 'RUNNING':
            if self.audio.done():
                if self.stage == 0 and self.pause_until is None:
                    # Playback has ended: never append an additional fade.
                    self.supply.off()
                    self.pause_until = now + self.config['zap_bell_pause_s']
                    self.log(f'Pause vor Kirchenglocke: {self.config["zap_bell_pause_s"]:g} s')
                if self.stage != 0 or now >= self.pause_until:
                    self.stage += 1
                    if self.stage == len(STAGES):
                        self.enter_locked()
                    else:
                        self.begin_stage()
            elif self.stage == 0:
                remaining = self.zap['duration_s'] - (now - self.stage_started)
                if not self.zap_fading:
                    if remaining <= self.config['zap_fade_out_s']:
                        self.supply.off(fade_s=self.config['zap_fade_out_s'],
                                        deadline=self.stage_started + self.zap['duration_s'])
                        self.zap_fading = True
                    else:
                        index = bisect.bisect_right(self.zap_times,
                                                   now - self.stage_started) - 1
                        if index >= 0 and index != self.event_index:
                            self.supply.current(self.zap['events'][index]['current_A'])
                            self.event_index = index
            elif self.stage == 2:
                # Full dark-to-bright pulses with an explicit peak plateau:
                # 100% must reach the fixture, not just a mathematical instant.
                elapsed = now - self.stage_started
                cfg = self.config['myers_lighting']
                color = cfg['colors'][int(elapsed / cfg['color_hold_s'])
                                      % len(cfg['colors'])]
                phase = elapsed % cfg['period_s']
                rise = (cfg['period_s'] - cfg['peak_hold_s']) / 2
                fraction = max(0, min(1, min(phase, cfg['period_s'] - phase) / rise))
                pulse = fraction * fraction * (3 - 2 * fraction)
                pulse = cfg['minimum_brightness'] + (1 - cfg['minimum_brightness']) * pulse
                self.lighting.color(scaled(color, cfg['brightness'] * pulse))
        elif self.state in ('LOCKED', 'RELEASING'):
            if self.voice and self.audio.done():
                self.voice = False
            if self.state == 'RELEASING' and not self.voice and not self.manual_powering:
                self.state = 'IDLE'
                self.locked_background = False
                self.locked_background_at = None
                self.audio.start(BACKGROUND)
                self.log('IDLE: Ansage vollständig beendet, Buzzer bereit')
            elif self.blink_started is not None:
                half = self.config['blink_half_period_s']
                step = int((now - self.blink_started) / half)
                if step >= 6:
                    self.blink_started = None
                    self.status_color(RED, fade=False)
                else:
                    self.status_color(RED if step % 2 else BLACK, fade=False)
            if (self.state == 'LOCKED' and not self.voice and not self.manual_powering
                    and self.locked_background_at is not None
                    and now >= self.locked_background_at and self.audio.done()):
                self.audio.start(BACKGROUND)
                self.locked_background = True
        self.supply.tick(now)
        self.lighting.tick(now)

    def stop(self):
        self.state = 'STOPPED'
        self.manual_powering = False
        self.manual_light_on = False
        self.locked_background = False
        self.locked_background_at = None
        # Always attempt every cleanup, even after an audio/USB/network error.
        try:
            self.audio.stop()
        finally:
            try:
                self.supply.close()
            finally:
                self.lighting.close()
