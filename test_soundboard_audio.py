import unittest

import numpy as np

from SoundBoard import ActiveClip, AudioEngine


class AudioEngineLiveMonitoringTests(unittest.TestCase):
    def test_selected_microphone_is_routed_to_output_in_real_time(self):
        engine = AudioEngine(lambda *args, **kwargs: None, lambda *args, **kwargs: None)
        engine.input_device = 0
        engine.output_level = 1.0
        engine.microphone_level = 1.0
        engine._mic_buffer = np.array([
            [0.4, 0.4],
            [0.8, 0.8],
        ], dtype="float32")

        outdata = np.zeros((2, 2), dtype="float32")
        engine._output_callback(outdata, 2, None, None)

        self.assertGreater(np.max(np.abs(outdata)), 0.0)

    def test_stop_sounds_silences_active_clips(self):
        engine = AudioEngine(lambda *args, **kwargs: None, lambda *args, **kwargs: None)
        engine._output_stream = object()
        engine.output_level = 1.0
        engine._clips.append(ActiveClip(np.ones((4, 2), dtype="float32")))

        engine.stop_sounds()
        outdata = np.zeros((2, 2), dtype="float32")
        engine._output_callback(outdata, 2, None, None)

        self.assertTrue(np.array_equal(outdata, np.zeros((2, 2), dtype="float32")))


if __name__ == "__main__":
    unittest.main()
