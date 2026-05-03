#!/usr/bin/env python
import sys
sys.path.insert(0, '/Users/natancichowicz/Downloads/ripo-blink-morse-translator-master-2/src')

from engine import MorseEngine
import config
import time

print('=== Testing Hysteresis Logic ===')
engine = MorseEngine()
engine.ready_to_start = True

# Start with eyes open
print('Initial state (eyes open, EAR=0.5):')
engine.update(0.5, 0.5)
print(f'  is_eye_closed={engine.is_eye_closed}, eye_open_hysteresis={engine.eye_open_hysteresis}')

# Simulate oscillating EAR (0.14, 0.16, 0.14, 0.16...) while eyes closing
print('\nSimulating oscillating EAR around threshold (0.14, 0.16, 0.14, 0.16):')

ear_values = [0.14, 0.16, 0.14, 0.16, 0.14, 0.16]
blink_count_before = len(engine.current_sequence)

for i, ear in enumerate(ear_values):
    engine.update(ear, ear)
    is_closed = engine.is_eye_closed
    hyst = engine.eye_open_hysteresis
    print(f'  Step {i+1}: EAR={ear:.2f} -> is_eye_closed={is_closed}, hysteresis={hyst}')

blink_count_after = len(engine.current_sequence)
print(f'\nOscillations detected as separate blinks: {blink_count_after - blink_count_before}')
print(f'Expected: 0 (oscylacje powinny być ignorowane)')

# Now properly open eyes
print('\nOpening eyes (EAR > 0.20):')
engine.update(0.25, 0.25)
is_closed = engine.is_eye_closed
hyst = engine.eye_open_hysteresis
print(f'  EAR=0.25 -> is_eye_closed={is_closed}, hysteresis={hyst}, sequence={repr(engine.current_sequence)}')

# Verify blink was counted once
print(f'\nTotal blinks recognized: {len(engine.current_sequence)} (should be 1 dot or dash)')

