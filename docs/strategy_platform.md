# Strategy Platform

All strategies implement a `BaseAgent` class which exposes:
- name
- version
- parameters
- regime compatibility

Strategies return standardized signals containing:
- action (BUY/SELL/HOLD)
- confidence
- attribution scores
