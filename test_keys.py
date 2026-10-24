"""Protocol fixtures, failure handling and restoration lifecycle checks."""
import contextlib
import importlib.machinery
import importlib.util
import io
import json
import os
from pathlib import Path
import stat
import struct
import tempfile
import unittest
from unittest.mock import patch

loader = importlib.machinery.SourceFileLoader('keyboard_keys', str(Path(__file__).with_name('keys')))
spec = importlib.util.spec_from_loader(loader.name, loader)
keys = importlib.util.module_from_spec(spec)
loader.exec_module(keys)
FIXTURES = json.loads((Path(__file__).parent / 'tests/fixtures/lighting.json').read_text())


class ProtocolTests(unittest.TestCase):
    def test_factory_style_reports_match_captured_stock_definitions(self):
        for slot in (2, 3):
            self.assertEqual(keys.factory_report(slot), bytes.fromhex(FIXTURES['factory'][str(slot)]['report']))
        for slot in (1, 4):
            with self.assertRaises(keys.KeysError):
                keys.factory_report(slot)

    def test_restore_defaults_touches_only_f2_and_f3_and_checks_readbacks(self):
        @contextlib.contextmanager
        def fake_fd(device=None):
            yield 7, 'device-identity'
        writes = []
        def exchange(fd, report, timeout=1.5, reply_size=None):
            slot = report[4] + 1
            self.assertIn(slot, (2, 3))
            if reply_size is None:
                writes.append(report)
                return None
            if report[3] == 0x31:
                saved = keys.factory_report(slot)
                return b'\x01' + saved[4:3 + reply_size]
            self.assertEqual(report[3], 0x38)
            return bytes([2, slot-1])
        with tempfile.TemporaryDirectory() as directory, patch.object(keys, 'STATE', Path(directory)), \
                patch.object(keys, 'lighting_fd', side_effect=fake_fd), patch.object(keys, 'exchange', side_effect=exchange), \
                contextlib.redirect_stdout(io.StringIO()):
            keys.restore_defaults()
        self.assertEqual([(p[3], p[4]) for p in writes], [(0x30, 1), (0x39, 1), (0x30, 2), (0x39, 2)])
    def test_lighting_reports_target_the_selected_profile(self):
        for slot in range(1, 5):
            for colour in ['#336699', 'off']:
                self.assertEqual(keys.report_for(colour, slot)[4], slot - 1)
            for mode in ['solid', 'fade', 'line', 'ripple']:
                self.assertEqual(keys.reactive_report(mode, '#FFD080', slot=slot)[4], slot - 1)
        with self.assertRaises(keys.KeysError):
            keys.report_for('#336699', 5)

    def test_apply_scene_never_overwrites_f2_or_f3(self):
        state = dict(keys.default_settings(), base='#9B68C7', scene=4, follow_slots=False)
        @contextlib.contextmanager
        def fake_fd(device):
            yield 7, 'device-identity'
        for slot in (2, 3):
            with patch.object(keys, 'lighting_fd', side_effect=fake_fd), \
                    patch.object(keys, 'query_slot', return_value=slot), patch.object(keys, 'exchange') as exchange:
                result, _ = keys.apply_scene(state, ('fake', 'device-identity'))
                self.assertTrue(result['passthrough'])
                exchange.assert_not_called()

    def test_apply_scene_follows_slot_change_inside_transaction(self):
        state = dict(keys.default_settings(), base='#9B68C7', scene=1, follow_slots=True)
        @contextlib.contextmanager
        def fake_fd(device):
            yield 7, 'device-identity'
        with patch.object(keys, 'lighting_fd', side_effect=fake_fd), \
                patch.object(keys, 'query_slot', return_value=4), patch.object(keys, 'exchange') as exchange:
            result, _ = keys.apply_scene(state, ('fake', 'device-identity'))
            self.assertEqual(result['scene'], 4)
            self.assertEqual([call.args[1][4] for call in exchange.call_args_list], [3, 3])
    def test_fd_identity_and_descriptor_validation(self):
        def ioctl(fd, request, buffer, mutate):
            if request == 0x80084803:
                struct.pack_into('=IHH', buffer, 0, 3, 0x1e71, 0x2105)
            elif request == 0x80044801:
                struct.pack_into('=I', buffer, 0, len(keys.DESCRIPTOR))
            elif request == 0x90044802:
                self.assertEqual(struct.unpack_from('=I', buffer)[0], len(keys.DESCRIPTOR))
                buffer[4:4 + len(keys.DESCRIPTOR)] = keys.DESCRIPTOR
            else:
                self.fail(f'Unexpected ioctl: {request:x}')
        info = os.stat_result((stat.S_IFCHR | 0o660, 0, 0, 0, 0, 0, 0, 0, 0, 0))
        with patch.object(keys.os, 'fstat', return_value=info), patch.object(keys.fcntl, 'ioctl', side_effect=ioctl):
            keys.validate_fd(7)
        def wrong_device(fd, request, buffer, mutate):
            struct.pack_into('=IHH', buffer, 0, 3, 0x05ac, 0x0291)
        with patch.object(keys.os, 'fstat', return_value=info), patch.object(keys.fcntl, 'ioctl', side_effect=wrong_device):
            with self.assertRaisesRegex(keys.KeysError, 'identity changed'):
                keys.validate_fd(7)

    def test_reports_match_independent_captures(self):
        for name, colour in [('red', '#FF0000'), ('green', '#00FF00'), ('blue', '#0000FF'), ('off', 'off')]:
            captured = [bytes.fromhex(p['report']) for p in FIXTURES['static'][name] if p['endpoint'] == 2]
            self.assertEqual(captured, [keys.report_for(colour)])

    def test_native_reactive_reports_match_captures(self):
        for mode, captured in FIXTURES['reactive'].items():
            self.assertEqual(keys.reactive_report(mode, '#FFFFFF', 70), bytes.fromhex(captured))

    def test_automatic_pairing_and_hex_colours(self):
        self.assertEqual(keys.paired_colour('#9B68C7'), '#FFFFFF')
        self.assertEqual(keys.paired_colour('#DFA0A0'), '#FFFFFF')
        self.assertEqual(keys.paired_colour('#FFFFFF'), '#343434')
        self.assertEqual(keys.paired_colour(keys.COLOURS['white']), '#343434')
        self.assertRegex(keys.paired_colour('#336699'), r'^#[0-9A-F]{6}$')

    def test_named_primaries_match_captured_full_intensity_reports(self):
        for name in ('red', 'green', 'blue'):
            captured = [bytes.fromhex(p['report']) for p in FIXTURES['static'][name] if p['endpoint'] == 2]
            self.assertEqual(captured, [keys.report_for(keys.parse_colour(name))])

    def test_colour_listing_does_not_access_hardware_or_settings(self):
        for command in ('colours', 'colors', 'list'):
            output = io.StringIO()
            with patch.object(keys.sys, 'argv', ['keys', command]), \
                    patch.object(keys, 'discover') as discover, patch.object(keys, 'locked') as locked, \
                    contextlib.redirect_stdout(output):
                self.assertEqual(keys.main(), 0)
            discover.assert_not_called()
            locked.assert_not_called()
            listed = dict(line.split() for line in output.getvalue().splitlines())
            self.assertEqual(listed, dict(keys.COLOURS, off='#000000'))

    def test_input_validation(self):
        self.assertEqual(keys.parse_colour('PiNk'), '#FF0080')
        self.assertEqual(keys.parse_colour('rose'), '#DFA0A0')
        self.assertEqual(keys.parse_colour('336699'), '#336699')
        self.assertEqual(keys.parse_colour('#aAbBcC'), '#AABBCC')
        self.assertEqual(keys.parse_colour('000000'), 'off')
        for value in ['rainbow', '#fff', '1234567', 'ff0000;reboot', '../off', '']:
            with self.assertRaises(keys.KeysError):
                keys.parse_colour(value)

    def transact(self, responses, writes=64, report=None):
        report = report or keys.report_for('#FF0000')
        reads = [BlockingIOError(), *responses]
        def read(fd, size):
            item = reads.pop(0)
            if isinstance(item, Exception):
                raise item
            return item
        with patch.object(keys.os, 'read', side_effect=read), patch.object(keys.os, 'write', return_value=writes), \
                patch.object(keys.select, 'select', side_effect=lambda *args: ([7], [], []) if reads else ([], [], [])):
            return keys.exchange(7, report, timeout=.01)

    def test_actual_hardware_response_format(self):
        # Responses here are from the independent TKL capture, which the live
        # MiniTKL also returned during the pink probe.
        incoming = [bytes.fromhex(p['report']) for p in FIXTURES['static']['red'] if p['endpoint'] == 0x82]
        self.transact(incoming)

    def test_echo_alone_is_not_success(self):
        echo = bytes.fromhex('43 e5') + keys.report_for('#FF0000')[2:]
        with self.assertRaisesRegex(keys.KeysError, 'did not acknowledge'):
            self.transact([echo])

    def test_acknowledgement_preserves_nonzero_profile_parameter(self):
        report = keys.report_for('#FF0000', slot=4)
        echo = bytes.fromhex('43 e5') + report[2:]
        acknowledgement = bytes.fromhex('43 82 00 01 03') + report[5:]
        self.transact([echo, acknowledgement], report=report)

    def test_rejection_disconnect_short_write(self):
        echo = bytes.fromhex('43 e5') + keys.report_for('#FF0000')[2:]
        reject = bytes.fromhex('43 82 00 00 00').ljust(64, b'\0')
        for responses, count in [([echo, reject], 64), ([b''], 64), ([b'bad'], 64), ([], 4)]:
            with self.assertRaises(keys.KeysError):
                self.transact(responses, count)


class StateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.state_patch = patch.object(keys, 'STATE', Path(self.temp.name) / 'state')
        self.state_patch.start()

    def tearDown(self):
        self.state_patch.stop()
        self.temp.cleanup()

    def test_failed_command_preserves_last_success(self):
        with keys.locked():
            keys.save_state('#DFA0A0', 'pink')
        before = (keys.STATE / 'state.json').read_bytes()
        with patch.object(keys, 'apply_scene', side_effect=keys.KeysError('no acknowledgement')):
            with self.assertRaises(keys.KeysError):
                keys.choose('blue')
        self.assertEqual((keys.STATE / 'state.json').read_bytes(), before)

    def test_discovery_ignores_input_interface_and_foreign_devices(self):
        sysfs = Path(self.temp.name) / 'hidraw'
        sysfs.mkdir()
        for index, vidpid, interface, descriptor in [
            (0, '1E71:2105', '00', b'normal keyboard'),
            (1, '1E71:2105', '01', keys.DESCRIPTOR),
            (2, '05AC:0291', '01', keys.DESCRIPTOR),
        ]:
            parent = Path(self.temp.name) / f'interface-{index}'
            hid = parent / 'hid'
            hid.mkdir(parents=True)
            (parent / 'bInterfaceNumber').write_text(interface + '\n')
            vendor, product = vidpid.split(':')
            (hid / 'uevent').write_text(f'HID_ID=0003:0000{vendor}:0000{product}\n')
            (hid / 'report_descriptor').write_bytes(descriptor)
            node = sysfs / f'hidraw{index}'
            node.mkdir()
            (node / 'device').symlink_to(hid)
        with patch.object(keys, 'SYSFS', sysfs):
            path, identity = keys.discover()
            self.assertEqual(path, Path('/dev/hidraw1'))
            self.assertTrue(identity.endswith('interface-1/hid'))

    def test_invalid_cli_input_never_opens_hardware(self):
        with patch.object(keys.sys, 'argv', ['keys', 'rainbow']), patch.object(keys, 'apply_scene') as apply, \
                contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(keys.main(), 2)
            apply.assert_not_called()

    def test_named_shortcut_dispatch(self):
        with patch.object(keys.sys, 'argv', ['keys-blue']), patch.object(keys, 'choose') as choose:
            self.assertEqual(keys.main(), 0)
            choose.assert_called_once_with('blue')

    def test_v1_migrates_without_enabling_new_features(self):
        with keys.locked():
            (keys.STATE / 'state.json').write_text(json.dumps({'version': 1, 'colour': '#9B68C7', 'label': 'purple'}))
            state = keys.read_state()
        self.assertEqual(state['base'], '#9B68C7')
        self.assertEqual(state['scene'], 1)
        self.assertFalse(state['follow_slots'])

    def test_fn_slot_following_switches_scene_without_repeated_writes(self):
        state = dict(keys.default_settings(), base='#9B68C7', colour='#9B68C7', follow_slots=True)
        with keys.locked():
            keys.save_state(state)
        watcher = keys.Restorer()
        with patch.object(keys, 'discover', return_value=(Path('/dev/hidraw1'), 'connection-1')), \
                patch.object(keys, 'get_slot', side_effect=[1, 1, 4, 4]), \
                patch.object(keys, 'apply_scene', side_effect=lambda settings, device: (settings, device[1])) as apply, \
                contextlib.redirect_stdout(io.StringIO()):
            for _ in range(4):
                watcher.step()
            self.assertEqual([call.args[0]['scene'] for call in apply.call_args_list], [1, 4])
            self.assertEqual(keys.read_state()['scene'], 4)

    def test_watcher_leaves_f2_and_f3_to_the_keyboard(self):
        state = dict(keys.default_settings(), base='#DFA0A0', colour='#DFA0A0', follow_slots=True)
        with keys.locked():
            keys.save_state(state)
        with patch.object(keys, 'discover', return_value=(Path('/dev/hidraw1'), 'connection-1')), \
                patch.object(keys, 'get_slot', side_effect=[2, 3]), \
                patch.object(keys, 'apply_scene') as apply, contextlib.redirect_stdout(io.StringIO()):
            watcher = keys.Restorer()
            watcher.step()
            watcher.step()
            apply.assert_not_called()

    def test_f4_automatic_colour_comes_from_the_theme_palette(self):
        palette = Path(self.temp.name) / 'palette.json'
        palette.write_text('{"accent":"#DFA0A0","foreground":"#E8E8E8","background":"#191919"}')
        state = dict(keys.default_settings(), base='theme', theme_path=str(palette))
        self.assertEqual(keys.paired_colour('#DFA0A0', state), '#E8E8E8')
        self.assertEqual(keys.paired_colour('#E8E8E8', state), '#191919')

    def test_theme_changes_preserve_scene_and_update_colour(self):
        palette = Path(self.temp.name) / 'palette.json'
        palette.write_text('{"accent":"#DFA0A0"}')
        state = dict(keys.default_settings(), base='theme', theme_path=str(palette), scene=4)
        with keys.locked():
            keys.save_state(state)
        def apply(settings, device):
            return dict(settings, colour=keys.resolve_base(settings)), device[1]
        watcher = keys.Restorer()
        with patch.object(keys, 'discover', return_value=(Path('/dev/hidraw1'), 'connection-1')), \
                patch.object(keys, 'apply_scene', side_effect=apply) as apply_mock, \
                contextlib.redirect_stdout(io.StringIO()):
            watcher.step()
            palette.write_text('{"accent":"#5C91D6"}')
            watcher.step()
            self.assertEqual(apply_mock.call_count, 2)
            saved = keys.read_state()
            self.assertEqual(saved['colour'], '#5C91D6')
            self.assertEqual(saved['scene'], 4)

    def test_invalid_palette_never_opens_hardware(self):
        palette = Path(self.temp.name) / 'palette.json'
        palette.write_text('{"accent":"not a colour"}')
        with patch.object(keys, 'apply_scene') as apply:
            with self.assertRaises(keys.KeysError):
                keys.configure(lambda settings: settings.update(base='theme', theme_path=str(palette)))
            apply.assert_not_called()

    def test_cli_rejects_invalid_scene_speed_and_effect(self):
        for args in [['scene', '2'], ['scene', '3'], ['scene', '5'], ['speed', '0'], ['speed', '101'], ['effect', 'invalid'], ['slots', 'invalid']]:
            with patch.object(keys.sys, 'argv', ['keys', *args]), patch.object(keys, 'configure') as configure, \
                    contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(keys.main(), 2)
                configure.assert_not_called()

    def test_restore_start_reconnect_and_foreground_change(self):
        with keys.locked():
            keys.save_state('#DFA0A0', 'pink')
        watcher = keys.Restorer()
        with patch.object(keys, 'discover', return_value=(Path('/dev/hidraw1'), 'connection-1')) as discover, \
                patch.object(keys, 'apply_scene', side_effect=lambda settings, device: (settings, device[1])) as apply, contextlib.redirect_stdout(io.StringIO()):
            watcher.step()
            watcher.step()
            self.assertEqual(apply.call_count, 1)
            with keys.locked():
                keys.save_state('#5C91D6', 'blue')  # foreground already applied it
            watcher.step()
            self.assertEqual(apply.call_count, 2)
            discover.return_value = (Path('/dev/hidraw7'), 'connection-2')
            watcher.step()
            self.assertEqual(apply.call_args.args[0]['colour'], '#5C91D6')
            self.assertEqual(apply.call_count, 3)

    def test_no_selection_makes_no_hardware_access(self):
        with patch.object(keys, 'discover') as discover:
            keys.Restorer().step()
            discover.assert_not_called()

    def test_invalid_saved_state_is_rejected(self):
        with keys.locked():
            (keys.STATE / 'state.json').write_text('{"version":1,"colour":"not hex"}')
            with self.assertRaises(keys.KeysError):
                keys.read_state()

    def test_failed_restore_retries_same_connection(self):
        with keys.locked():
            keys.save_state('off', 'off')
        watcher = keys.Restorer()
        with patch.object(keys, 'discover', return_value=(Path('/dev/hidraw1'), 'connection-1')), \
                patch.object(keys, 'apply_scene', side_effect=[keys.KeysError('permission'), (dict(keys.default_settings(), base='off', colour='off'), 'connection-1')]) as apply, \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            try:
                watcher.step()
            except keys.KeysError as exc:
                watcher.failed(exc)
            watcher.step()
            self.assertEqual(apply.call_count, 2)


if __name__ == '__main__':
    unittest.main()
