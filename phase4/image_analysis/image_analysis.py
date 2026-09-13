# ============================================
# PHASE 4.2 - CITIZEN IMAGE ANALYSIS
# ============================================

print("\n============================================")
print("       PHASE 4.2 - IMAGE ANALYSIS")
print("============================================\n")


# Simulated citizen image result
# This is a TEST version.
# Later we will connect a real AI image model.

image_result = {
    "landslide": False,
    "flooding": True,
    "road_damage": False
}


# ============================================
# ANALYZE IMAGE RESULT
# ============================================

detected_conditions = []

if image_result["landslide"]:
    detected_conditions.append("LANDSLIDE")

if image_result["flooding"]:
    detected_conditions.append("FLOODING")

if image_result["road_damage"]:
    detected_conditions.append("ROAD DAMAGE")


# ============================================
# DISPLAY ANALYSIS
# ============================================

print("Citizen Image Analysis:")

if detected_conditions:
    for condition in detected_conditions:
        print(f"Detected: {condition}")
else:
    print("No disaster condition detected.")


# ============================================
# GENERATE WARNING
# ============================================

print("\n============================================")
print("              WARNING STATUS")
print("============================================")


if detected_conditions:
    print("WARNING: Potential disaster condition detected!")
    print("Conditions:", ", ".join(detected_conditions))
else:
    print("STATUS: No immediate danger detected.")


# ============================================
# END
# ============================================

print("\n============================================")
print("       IMAGE ANALYSIS COMPLETED")
print("============================================\n")