from enum import Enum


class MaterialCategory(str, Enum):
    timber = "timber"
    board = "board"
    osb = "osb"
    insulation = "insulation"
    concrete = "concrete"
    metal = "metal"
    roofing = "roofing"
    windows = "windows"