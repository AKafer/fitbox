from typing import Dict


class SensorsState:
    def __init__(self) -> None:
        self.devices: Dict[str, str] = {}
        self.training_active: bool = False