import sys

sys.path.insert(0, "d:/Projects/Crickplay")

from src.medallion.cdc import CDCManager, CDCConfig

print("CDC imports OK")

cdc = CDCManager()
print("CDC initialized:", cdc.get_stats())
